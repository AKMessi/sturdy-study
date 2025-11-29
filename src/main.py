from fastapi import FastAPI
from src.core.config import settings
import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # <--- NEW IMPORT
from src.api.v1.endpoints import study 

app = FastAPI(
    title="Student SaaS AI Agent",
    description="A production-ready API for our study agent.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://sturdystudy.online",      
        "https://www.sturdystudy.online",  
        "*"                                
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
if not os.path.exists(os.path.join(static_dir, "exams")):
    os.makedirs(os.path.join(static_dir, "exams"))

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(study.router, prefix="/v1/study", tags=["Study API"])

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Service is running."}