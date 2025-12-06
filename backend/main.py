import sys
import os

# Fix Protocol: Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Import routers
from api import satellite
from api import sentinelhub

# Load environment
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SattelishMaps Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "service": "SattelishMaps Backend (Integrated)"}

# Mount Routers
# 1. Existing Copernicus/Supabase Router
app.include_router(satellite.router, prefix="/api", tags=["Satellite (Copernicus)"])

# 2. New SentinelHub Router
# We mount this specifically to handle the "bounds/search" which might overlap or extend satellite-data
# The frontend calls /api/satellite-data/bounds/search
# My sentinelhub.py defines /bounds/search
# So we mount it under /api/satellite-data
app.include_router(sentinelhub.router, prefix="/api/satellite-data", tags=["SentinelHub"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
