import os
from pydantic_settings import BaseSettings

class CommonSettings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "Preqin-APIs")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "True").strip().lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "prqin_api.log")

class ServerSettings(BaseSettings):
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

class DatabaseSettings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://preetykumari2402:w3fGZoPuUXdZiHod@preety-cluster.osy9vib.mongodb.net/")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "preqin_dev_db")

    # Collection Names
    INVESTORS_COLLECTION: str = "investors"

# Main Settings class that combines all configuration
class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass

settings = Settings()
