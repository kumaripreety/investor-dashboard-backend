from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from apis.investors.investor_enums import AssetClassEnum, CountryEnum, CurrencyEnum, InvestorTypeEnum
from apis.utils.util_models import ModelId


class CommitmentModel(BaseModel):
    asset_class: AssetClassEnum
    amount: Decimal
    currency: CurrencyEnum

    class Config:
        json_encoders = {Decimal: float}
        use_enum_values = True


class InvestorBaseModel(BaseModel):
    name: str
    investor_type: InvestorTypeEnum
    country: str
    date_added: datetime
    last_updated: datetime
    address: Optional[str] = None  # Added address field
    commitments: List[CommitmentModel] = []

    class Config:
        json_encoders = {Decimal: float}
        use_enum_values = True


# Entity Class
class InvestorModel(InvestorBaseModel):
    class Config:
        extra = "ignore"
        json_encoders = {Decimal: float}
        use_enum_values = True


# Investor Request Models
class InvestorCreateModel(BaseModel):
    name: str
    investor_type: InvestorTypeEnum
    country: str
    address: Optional[str] = None  # Added address field
    commitments: List[CommitmentModel] = []

    class Config:
        extra = "ignore"
        json_encoders = {Decimal: float}
        use_enum_values = True


# Updated Response Models with date_added and address
class InvestorResponseModel(InvestorModel, ModelId):
    total_commitment_usd: Optional[Decimal] = None

    class Config:
        json_encoders = {Decimal: float}
        use_enum_values = True


class InvestorSummaryModel(BaseModel):
    id: str
    name: str
    investor_type: InvestorTypeEnum
    country: str
    date_added: datetime  # Added date_added field
    address: Optional[str] = None  # Added address field
    total_commitment_usd: Decimal
    commitment_count: int

    class Config:
        json_encoders = {Decimal: float}
        use_enum_values = True


class InvestorCommitmentDetailModel(BaseModel):
    id: str
    name: str
    investor_type: InvestorTypeEnum
    country: str
    date_added: datetime  # Added date_added field
    address: Optional[str] = None  # Added address field
    commitments: List[CommitmentModel]
    total_commitment_usd: Decimal

    class Config:
        json_encoders = {Decimal: float}
        use_enum_values = True


class CSVUploadResponseModel(BaseModel):
    message: str
    total_investors: int
    total_commitments: int
    success: bool


class InvestorFilterModel(BaseModel):
    asset_class: Optional[AssetClassEnum] = None
    investor_type: Optional[InvestorTypeEnum] = None
    country: Optional[CountryEnum] = None
    min_commitment: Optional[Decimal] = None
    max_commitment: Optional[Decimal] = None
