from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
