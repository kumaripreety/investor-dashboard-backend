# src/main.py
import logging

from fastapi.responses import RedirectResponse
import uvicorn
from config.server import app
from config.setup import settings
from apis.investors.investor_routers import router as investor_router

V1_APIS = "/api/v1"


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

app.include_router(investor_router)


if __name__ == "__main__":
    logging.info(f"Starting {settings.APP_NAME}")
    logging.info(f"Server: http://{settings.HOST}:{settings.PORT}")

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG_MODE, log_level=settings.LOG_LEVEL.lower())
