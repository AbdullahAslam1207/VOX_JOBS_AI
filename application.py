import httpx
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from Routes.fetch_mustaqbil_jobs import fetch_jobs
from Routes.fetch_jobz_jobs import fetch_jobz_jobs
from Security.security import verify_api_key
import os

load_dotenv()

application = FastAPI()

# Enable CORS for all origins (customize as needed)
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@application.get("/")
def home():
    return {"message": "Welcome to VoxJobs AI home route!"}




@application.get("/fetch_jobs_mustaqbil")
async def fetch_jobs_mustaqbil(api_key: str = Depends(verify_api_key)):
    result = await fetch_jobs()
    return result


@application.get("/fetch_jobs_jobz")
async def fetch_jobs_jobz(api_key: str = Depends(verify_api_key)):
    result = await fetch_jobz_jobs()
    return result
    
