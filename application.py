import httpx
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from Routes.fetch_mustaqbil_jobs import fetch_jobs
from Routes.fetch_jobz_jobs import fetch_jobz_jobs
from Security.security import verify_api_key
from Routes.get_jobs_data import fetch_and_save_jobs
from Routes.vector_store import create_chroma_db_from_jobs
from utils.load_model import load_jobs_vector_store
from utils.chat_function import chat_jobs
from utils.rephrase_query import rephrase_question_jobs
from utils.jobs_prompts import rephrase_query_prompt_jobs
from utils.normalize_history import clean_and_parse
import subprocess
import os
import requests
import sys



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
    


@application.get("/create_vector_store")
async def create_vector_store():
    #first get data 
    print("Vector store creation started...")
    result = fetch_and_save_jobs()

    #then create vector store
    result = create_chroma_db_from_jobs()
    return result



@application.post("/chat_response_jobs")
async def chat_response_jobs(request: Request):
    """
    Chat endpoint for Jobs chatbot using jobs_store vector store.
    Provides job search responses based on job listings database.
    Does not use streaming - returns complete response.
    """
    print("chat api jobs is hit")
    
    # Step 1: Parse request
    data = await request.json()
    chat_history = data.get("user_query", [])
    query = data.get("query", "")
    
    # Step 2: Rephrase query based on chat history
    if chat_history:
        previous_user_message = chat_history[-1].get("userMessage", "")
        previous_bot_message = chat_history[-1].get("botResponse", "")
    else:
        previous_user_message = ""
        previous_bot_message = ""
    
    # print(f"Received jobs query: {query}")
    # print(f"Previous message: {previous_user_message}")
    
    if previous_bot_message:
        previous_bot_message = clean_and_parse(previous_bot_message)
        print(f"clean bot message: {previous_bot_message}")
        
        # Create rephrase prompt for jobs using job-specific prompt
        updated_rephrase_query_prompt_jobs = rephrase_query_prompt_jobs.replace("{previous_query}", previous_user_message)
        updated_rephrase_query_prompt_jobs = updated_rephrase_query_prompt_jobs.replace("{previous_bot_response}", previous_bot_message)
        
        # Rephrase the query using job-specific function
        query = rephrase_question_jobs(updated_rephrase_query_prompt_jobs, query)
        print(f"rephrased jobs query: {query}")

    # Step 3: Load vector store
    retriever = load_jobs_vector_store()
    if retriever is None:
        return {
            "response": "",
            "status": 500,
            "error": "Failed to load jobs vector store"
        }

    retriever = retriever.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    print("Jobs ChromaDB retriever loaded successfully")

    try:
        return chat_jobs(chat_history, retriever, query)
    except Exception as e:
        print(f"The error is {str(e)}")
        return {"response": "", "status": 500, "error": str(e)}

