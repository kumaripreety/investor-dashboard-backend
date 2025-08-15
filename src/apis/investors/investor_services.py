import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO
import logging
import random
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from apis.investors.investor_enums import AssetClassEnum, CurrencyEnum, InvestorTypeEnum
from apis.investors.investor_models import (
    CommitmentModel,
    CSVUploadResponseModel,
    InvestorCommitmentDetailModel,
    InvestorFilterModel,
    InvestorModel,
    InvestorSummaryModel,
)
from config.setup import settings

# Currency conversion rates (simplified - only GBP to USD since data only has GBP)
CURRENCY_TO_USD_RATES = {"GBP": 1.25, "USD": 1.0}


def convert_to_usd(amount: Decimal, currency: str) -> Decimal:
    """Convert amount from given currency to USD"""
    rate = CURRENCY_TO_USD_RATES.get(currency, 1.0)
    return amount * Decimal(str(rate))


def generate_mock_address(country: str, investor_name: str) -> str:
    """Generate mock address based on country"""
    addresses = {
        "United Kingdom": [
            "Baker Street, London",
            "Piccadilly, London",
            "Oxford Street, London",
            "Regent Street, London",
            "Canary Wharf, London",
            "The City, London",
        ],
        "United States": [
            "Fifth Avenue, New York",
            "Wall Street, New York",
            "Madison Avenue, New York",
            "Broadway, New York",
            "Park Avenue, New York",
            "Times Square, New York",
        ],
        "Singapore": [
            "Marina Bay, Singapore",
            "Orchard Road, Singapore",
            "Raffles Place, Singapore",
            "Sentosa Island, Singapore",
            "Clarke Quay, Singapore",
            "Chinatown, Singapore",
        ],
        "China": [
            "Nathan Road, Hong Kong",
            "Central District, Hong Kong",
            "Tsim Sha Tsui, Hong Kong",
            "Causeway Bay, Hong Kong",
            "Admiralty, Hong Kong",
            "Wan Chai, Hong Kong",
        ],
    }

    country_addresses = addresses.get(country, [f"Main Street, {country}"])
    # Use hash of investor name for consistent address assignment
    hash_value = hash(investor_name) % len(country_addresses)
    street_number = (hash(investor_name) % 100) + 1

    return f"{street_number} {country_addresses[hash_value]}"


async def upload_csv_data(db: AsyncIOMotorDatabase, file: UploadFile) -> CSVUploadResponseModel:
    """Upload and process CSV file with investor data"""
    logging.info(f"Processing CSV upload: {file.filename}")

    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode("utf-8")
        csv_reader = csv.DictReader(StringIO(csv_content))

        # Group commitments by investor
        investors_data = {}
        total_commitments = 0

        for row in csv_reader:
            investor_name = row["Investor Name"].strip()

            # Parse dates
            try:
                date_added = datetime.strptime(row["Investor Date Added"].strip(), "%Y-%m-%d")
                last_updated = datetime.strptime(row["Investor Last Updated"].strip(), "%Y-%m-%d")
            except ValueError:
                # Fallback for different date formats
                try:
                    date_added = datetime.strptime(row["Investor Date Added"].strip(), "%m/%d/%Y")
                    last_updated = datetime.strptime(row["Investor Last Updated"].strip(), "%m/%d/%Y")
                except ValueError:
                    # Ultimate fallback
                    date_added = datetime.now()
                    last_updated = datetime.now()

            # Create commitment
            commitment = CommitmentModel(
                asset_class=AssetClassEnum(row["Commitment Asset Class"].strip()),
                amount=Decimal(str(row["Commitment Amount"])),
                currency=CurrencyEnum(row["Commitment Currency"].strip()),
            )

            # Group by investor
            if investor_name not in investors_data:
                # Generate mock address if not provided in CSV
                address = row.get("Investor Address", "").strip()
                if not address:
                    address = generate_mock_address(row["Investor Country"].strip(), investor_name)

                investors_data[investor_name] = {
                    "name": investor_name,
                    "investor_type": InvestorTypeEnum(row["Investory Type"].strip()),  # Note: CSV has typo "Investory"
                    "country": row["Investor Country"].strip(),
                    "date_added": date_added,
                    "last_updated": last_updated,
                    "address": address,
                    "commitments": [],
                }

            investors_data[investor_name]["commitments"].append(commitment)
            total_commitments += 1

        # Clear existing data and insert new data
        await db[settings.INVESTORS_COLLECTION].delete_many({})

        # Create investor documents
        investor_docs = []
        for investor_data in investors_data.values():
            investor_model = InvestorModel(**investor_data)
            # Convert to dict and handle serialization
            doc = investor_model.model_dump(exclude_none=True)

            # Convert enums to their string values and Decimals to float
            doc["investor_type"] = doc["investor_type"].value if hasattr(doc["investor_type"], "value") else doc["investor_type"]

            # Convert commitments
            for commitment in doc["commitments"]:
                commitment["asset_class"] = (
                    commitment["asset_class"].value if hasattr(commitment["asset_class"], "value") else commitment["asset_class"]
                )
                commitment["currency"] = (
                    commitment["currency"].value if hasattr(commitment["currency"], "value") else commitment["currency"]
                )
                commitment["amount"] = float(commitment["amount"])

            investor_docs.append(doc)

        # Insert all investors
        if investor_docs:
            await db[settings.INVESTORS_COLLECTION].insert_many(investor_docs)

            # Create indexes for better query performance using Motor
            await db[settings.INVESTORS_COLLECTION].create_index("name")
            await db[settings.INVESTORS_COLLECTION].create_index("country")
            await db[settings.INVESTORS_COLLECTION].create_index("commitments.asset_class")
            await db[settings.INVESTORS_COLLECTION].create_index("date_added")

        logging.info(f"Successfully uploaded {len(investors_data)} investors with {total_commitments} commitments")

        return CSVUploadResponseModel(
            message="CSV data uploaded successfully",
            total_investors=len(investors_data),
            total_commitments=total_commitments,
            success=True,
        )

    except Exception as ex:
        logging.error(f"Error processing CSV upload: {ex}")
        raise HTTPException(500, f"Error processing CSV file: {str(ex)}") from ex


async def get_investors_summary(db: AsyncIOMotorDatabase, filters: Optional[InvestorFilterModel] = None) -> List[InvestorSummaryModel]:
    """Get summary of all investors with their total commitments - No filtering applied here since filters moved to details page"""
    logging.info("Fetching investors summary")

    try:
        # Simplified pipeline - no filtering since filters are now in details page
        # Just get all investors with their basic info and totals
        pipeline = [
            {
                "$addFields": {
                    "total_commitment_usd": {
                        "$sum": {
                            "$map": {
                                "input": "$commitments",
                                "as": "commitment",
                                "in": {
                                    "$multiply": [
                                        "$$commitment.amount",
                                        {
                                            "$switch": {
                                                "branches": [
                                                    {"case": {"$eq": ["$$commitment.currency", "GBP"]}, "then": 1.25},
                                                    {"case": {"$eq": ["$$commitment.currency", "USD"]}, "then": 1.0},
                                                ],
                                                "default": 1.25,
                                            }
                                        },
                                    ]
                                },
                            }
                        }
                    },
                    "commitment_count": {"$size": "$commitments"},
                }
            },
            # Sort by total commitment (descending)
            {"$sort": {"total_commitment_usd": -1}},
            # Project final fields including date_added and address
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "name": 1,
                    "investor_type": 1,
                    "country": 1,
                    "date_added": 1,
                    "address": {"$ifNull": ["$address", None]},
                    "total_commitment_usd": 1,
                    "commitment_count": 1,
                }
            },
        ]

        cursor = db[settings.INVESTORS_COLLECTION].aggregate(pipeline)
        investors = await cursor.to_list(length=None)

        return [InvestorSummaryModel(**investor) for investor in investors]

    except Exception as ex:
        logging.error(f"Error fetching investors summary: {ex}")
        raise HTTPException(500, f"Error fetching investors summary: {str(ex)}") from ex


async def get_investor_details(db: AsyncIOMotorDatabase, investor_id: str) -> InvestorCommitmentDetailModel:
    """Get detailed view of a specific investor with all commitments"""
    logging.info(f"Fetching details for investor: {investor_id}")

    try:
        # Aggregation pipeline to get investor with calculated total
        pipeline = [
            {"$match": {"_id": ObjectId(investor_id)}},
            {
                "$addFields": {
                    "total_commitment_usd": {
                        "$sum": {
                            "$map": {
                                "input": "$commitments",
                                "as": "commitment",
                                "in": {
                                    "$multiply": [
                                        "$$commitment.amount",
                                        {
                                            "$switch": {
                                                "branches": [
                                                    {"case": {"$eq": ["$$commitment.currency", "GBP"]}, "then": 1.25},
                                                    {"case": {"$eq": ["$$commitment.currency", "USD"]}, "then": 1.0},
                                                ],
                                                "default": 1.25,
                                            }
                                        },
                                    ]
                                },
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "name": 1,
                    "investor_type": 1,
                    "country": 1,
                    "date_added": 1,
                    "address": {"$ifNull": ["$address", None]},
                    "commitments": 1,
                    "total_commitment_usd": 1,
                }
            },
        ]

        cursor = db[settings.INVESTORS_COLLECTION].aggregate(pipeline)
        investors = await cursor.to_list(length=1)

        if not investors:
            raise HTTPException(404, f"Investor with id {investor_id} not found")

        return InvestorCommitmentDetailModel(**investors[0])

    except Exception as ex:
        if isinstance(ex, HTTPException):
            raise
        logging.error(f"Error fetching investor details for {investor_id}: {ex}")
        raise HTTPException(500, f"Error fetching investor details: {str(ex)}") from ex


async def get_asset_classes(db: AsyncIOMotorDatabase) -> List[str]:
    """Get all unique asset classes from the database"""
    logging.info("Fetching unique asset classes")

    try:
        pipeline = [{"$unwind": "$commitments"}, {"$group": {"_id": "$commitments.asset_class"}}, {"$sort": {"_id": 1}}]

        cursor = db[settings.INVESTORS_COLLECTION].aggregate(pipeline)
        asset_classes = await cursor.to_list(length=None)

        return [ac["_id"] for ac in asset_classes if ac["_id"]]

    except Exception as ex:
        logging.error(f"Error fetching asset classes: {ex}")
        raise HTTPException(500, f"Error fetching asset classes: {str(ex)}") from ex
