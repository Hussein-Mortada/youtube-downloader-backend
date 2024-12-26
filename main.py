import os

from fastapi import FastAPI
from routers import fetch, downloadaudio, downloadvideo, incrementdownload
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")  # Default to localhost if not set

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Add `download_count` to the app state
app.state.download_count = 0

# Register routers
app.include_router(fetch.router, prefix="/api")
app.include_router(downloadaudio.router, prefix="/api")
app.include_router(downloadvideo.router, prefix="/api")
app.include_router(incrementdownload.router, prefix="/api")
