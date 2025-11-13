from fastapi import FastAPI
from src.core.config import settings
import os
from src.api.v1.endpoints import study 

app = FastAPI(
    title="Student SaaS AI Agent",
    description="A production-ready API for our study agent.",
    version="0.1.0"
)

app.include_router(study.router, prefix="/v1/study", tags=["Study API"])

@app.get("/", tags=["Health Check"])
async def root():
    """
    A simple health check endpoint.
    """
    return {"status": "ok", "message": "Service is running."}