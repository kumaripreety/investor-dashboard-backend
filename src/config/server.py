# src/config/server.py
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dependencies.mongo_db_client import MongoDBClient


@asynccontextmanager
async def lifespan(fast_api: FastAPI):
    logging.info("Starting the Blog-APIs")

    try:
        # Initialise clients (dependencies)
        fast_api.state.mongodb_client = MongoDBClient()
        yield
    except Exception as ex:
        logging.error(f"Failed to initialise {ex}")
        raise
    finally:
        logging.info("Shutting Down")
        await fast_api.state.mongodb_client.close()
        logging.info("MongoDB connection closed")


# Create a FastAPI APP
app = FastAPI(
    lifespan=lifespan,
    title="Preety Blog APIs",
    description="APIs for Blogging Application",
    version="1.0.0",
    contact={"name": "Preety", "email": "preetykumari2402@gmail.com"},
)

# CORS
origins = ["http://localhost:3000"]

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
