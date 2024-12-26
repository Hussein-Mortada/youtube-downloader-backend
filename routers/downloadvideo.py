import logging

from fastapi import APIRouter, BackgroundTasks
from yt_dlp import YoutubeDL
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from urllib.parse import quote
import re

router = APIRouter()

class DownloadRequest(BaseModel):
    url: str
    media_type: str  # "audio" or "video"
    quality: str = None  # Optional, e.g., "144p", "360p", etc.

def delete_file(file_path: str):
    """Delete the file from the server."""
    if os.path.exists(file_path):
        os.remove(file_path)

def sanitize_filename(title: str):
    # Replace invalid characters with an underscore
    return re.sub(r'[<>:"/\\|?*\x00-\x1F\x7F#%&\'\"`¥]', '', title)


@router.post("/downloadvideo")
def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    os.makedirs('downloads', exist_ok=True)  # Ensure output directory exists
    quality_prefix = sanitize_filename(f"{request.quality} - ") if request.quality else ""

    ydl_opts = {
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'format': f"bestvideo[height={request.quality[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best"
        if request.quality
        else "bestvideo+bestaudio/best",
        'outtmpl': f'downloads/%(id)s.%(ext)s',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(request.url, download=True)

        original_title = info_dict['title']
        print(f"Original title: {original_title}")

        # Sanitize the filename to remove invalid characters
        sanitized_title = sanitize_filename(original_title)
        print(f"Sanitized title: {sanitized_title}")

        downloaded_file_path = f"downloads/{info_dict['id']}.mp4"

        if not os.path.exists(downloaded_file_path):
            return {"error": "Downloaded file not found."}

        # Rename the downloaded file to the sanitized title
        sanitized_file_path = f"downloads/{sanitized_title}.mp4"
        os.rename(downloaded_file_path, sanitized_file_path)
        print(f"Renamed file to: {sanitized_file_path}")


        background_tasks.add_task(delete_file, sanitized_file_path)
        url_encoded_title = quote(sanitized_title)  # URL encode for HTTP

        return FileResponse(
            sanitized_file_path,
            media_type="video/mp4",
            filename=f"{url_encoded_title}.mp4",
            headers={"Content-Disposition": f'attachment; filename="{url_encoded_title}.mp4"'}
        )

    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return {"error": "Failed to process the download. Please try again later."}