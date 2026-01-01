import logging
import os
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arkadia")

app = FastAPI(title="Arkadia Console (Cycle 11)")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://*.vercel.app"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/heartbeat")
async def heartbeat():
    """The Heartbeat of the Distributed Monastery."""
    return {"status": "radiant", "resonance": 0.99, "render_url": "https://arkadia-n26k.onrender.com"}

@app.get("/")
async def root():
    return {"message": "Arkadia Mind (API) is online and breathing."}
