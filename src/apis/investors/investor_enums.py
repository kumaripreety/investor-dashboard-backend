from enum import Enum


class InvestorTypeEnum(str, Enum):
    ASSET_MANAGER = "asset manager"
    BANK = "bank"
    FUND_MANAGER = "fund manager"
    WEALTH_MANAGER = "wealth manager"


class AssetClassEnum(str, Enum):
    HEDGE_FUNDS = "Hedge Funds"
    INFRASTRUCTURE = "Infrastructure"
    NATURAL_RESOURCES = "Natural Resources"
    PRIVATE_DEBT = "Private Debt"
    PRIVATE_EQUITY = "Private Equity"
    REAL_ESTATE = "Real Estate"


class CurrencyEnum(str, Enum):
    GBP = "GBP"
    USD = "USD"  # Added USD support


class CountryEnum(str, Enum):
    CHINA = "China"
    SINGAPORE = "Singapore"
    UNITED_KINGDOM = "United Kingdom"
    UNITED_STATES = "United States"

