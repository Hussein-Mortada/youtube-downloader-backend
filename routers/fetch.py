from fastapi import APIRouter
from yt_dlp import YoutubeDL
from pydantic import BaseModel

router = APIRouter()

class VideoRequest(BaseModel):
    url: str

@router.post("/fetch-details")
def fetch_details(request: VideoRequest):
    """
    Fetch metadata for a given YouTube URL.
    """
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,  # Prevents fetching entire playlist
        "playlist_items": "1",  # Fetch only the first video in a playlist
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(request.url, download=False)
    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "formats": [
            {
                "format_id": f.get("format_id"),
                "format_note": f.get("format_note", "N/A"),  # Use "N/A" if `format_note` is missing
                "ext": f.get("ext")
            }
            for f in info.get("formats", [])  # Use an empty list if `formats` is missing
        ]
    }
