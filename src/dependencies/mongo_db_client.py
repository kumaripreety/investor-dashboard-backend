import logging

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config.setup import settings


class MongoDBClient:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.database = self.client[settings.MONGO_DB_NAME]
        logging.info("MongoDB initialised successfully")

    def get_database(self) -> AsyncIOMotorDatabase:
        return self.database

    async def close(self):
        self.client.close()

async def get_mongo_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.mongodb_client.get_database()
