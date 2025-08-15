from decimal import Decimal
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from apis.investors.investor_enums import AssetClassEnum, CountryEnum, InvestorTypeEnum
from apis.investors.investor_models import CSVUploadResponseModel, InvestorCommitmentDetailModel, InvestorFilterModel, InvestorSummaryModel
from apis.investors.investor_services import get_asset_classes, get_investor_details, get_investors_summary, upload_csv_data
from config.setup import settings
from dependencies.mongo_db_client import get_mongo_db

router = APIRouter(prefix="/investors", tags=["Investors"])


@router.post("/upload-csv", response_model=CSVUploadResponseModel)
async def upload_investor_csv(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Upload CSV file with investor data"""
    logging.info(f"Received request to upload CSV file: {file.filename}")

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are allowed")

    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(400, "File size too large. Maximum 10MB allowed")

    try:
        return await upload_csv_data(db, file)
    except Exception as ex:
        raise HTTPException(500, f"Server Error while uploading CSV: {str(ex)}") from ex


@router.get("/summary", response_model=List[InvestorSummaryModel])
async def get_investors_list(
    # Removed filter parameters since filtering is now done in the frontend for individual investor commitments
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get list of all investors with their total commitments (no filters - filtering moved to details page)"""
    logging.info("Received request to fetch investors summary")

    try:
        # No filters applied here - get all investors
        return await get_investors_summary(db, None)
    except Exception as ex:
        raise HTTPException(500, f"Server Error while fetching investors: {str(ex)}") from ex


@router.get("/{investor_id}/details", response_model=InvestorCommitmentDetailModel)
async def get_investor_commitment_details(investor_id: str, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Get detailed breakdown of commitments for a specific investor (filtering happens in frontend)"""
    logging.info(f"Received request to fetch details for investor: {investor_id}")

    try:
        return await get_investor_details(db, investor_id)
    except Exception as ex:
        if isinstance(ex, HTTPException):
            raise
        raise HTTPException(500, f"Server Error while fetching investor details: {str(ex)}") from ex


@router.get("/asset-classes", response_model=List[str])
async def get_available_asset_classes(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Get all unique asset classes available in the database"""
    logging.info("Received request to fetch available asset classes")

    try:
        return await get_asset_classes(db)
    except Exception as ex:
        raise HTTPException(500, f"Server Error while fetching asset classes: {str(ex)}") from ex


# Additional utility endpoints
@router.get("/stats")
async def get_investment_stats(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Get overall investment statistics"""
    logging.info("Received request to fetch investment statistics")

    try:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_investors": {"$sum": 1},
                    "total_commitments": {"$sum": {"$size": "$commitments"}},
                    "unique_countries": {"$addToSet": "$country"},
                    "unique_asset_classes": {"$addToSet": "$commitments.asset_class"},
                    "total_commitment_amount": {
                        "$sum": {
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
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_investors": 1,
                    "total_commitments": 1,
                    "unique_countries_count": {"$size": "$unique_countries"},
                    "unique_countries": 1,
                    "total_commitment_amount_usd": 1,
                }
            },
        ]

        cursor = db[settings.INVESTORS_COLLECTION].aggregate(pipeline)
        stats = await cursor.to_list(length=1)

        if not stats:
            return {
                "total_investors": 0,
                "total_commitments": 0,
                "unique_countries_count": 0,
                "unique_countries": [],
                "total_commitment_amount_usd": 0,
            }

        return stats[0]

    except Exception as ex:
        raise HTTPException(500, f"Server Error while fetching statistics: {str(ex)}") from ex


# Optional: Legacy endpoint with filters (for backward compatibility)
@router.get("/summary-filtered", response_model=List[InvestorSummaryModel])
async def get_investors_list_with_filters(
    asset_class: Optional[AssetClassEnum] = Query(None, description="Filter by asset class"),
    investor_type: Optional[InvestorTypeEnum] = Query(None, description="Filter by investor type"),
    country: Optional[CountryEnum] = Query(None, description="Filter by country"),
    min_commitment: Optional[Decimal] = Query(None, description="Minimum total commitment in USD"),
    max_commitment: Optional[Decimal] = Query(None, description="Maximum total commitment in USD"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Legacy endpoint: Get list of investors with filters (kept for backward compatibility)"""
    logging.info("Received request to fetch investors summary with filters")

    try:
        # Create filter model
        filters = InvestorFilterModel(
            asset_class=asset_class,
            investor_type=investor_type,
            country=country,
            min_commitment=min_commitment,
            max_commitment=max_commitment,
        )

        # Note: You would need to implement the filtering logic in get_investors_summary
        # if you want to keep this endpoint functional
        return await get_investors_summary(db, filters)
    except Exception as ex:
        raise HTTPException(500, f"Server Error while fetching investors: {str(ex)}") from ex
