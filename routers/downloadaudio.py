import re
import os
import subprocess
import shutil
import requests
from yt_dlp import YoutubeDL
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
from urllib.parse import quote

router = APIRouter()

class DownloadRequest(BaseModel):
    url: str
    media_type: str  # "audio" or "video"
    bitrate: str = "128"  # For audio: "96", "128", etc.

def delete_file(file_path: str):
    """Delete the file from the server."""
    if os.path.exists(file_path):
        os.remove(file_path)

# Safe filename normalization function to handle invalid characters
def sanitize_filename(title: str):
    # Replace invalid characters with an underscore
    return re.sub(r'[<>:"/\\|?*\x00-\x1F\x7F#%&\'\"`¥]', '', title)


@router.post("/downloadaudio")
def download_audio(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Download audio from YouTube based on user preferences and convert to MP3 with thumbnail.
    """
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',  # Use video ID for a generic name
        'format': 'bestaudio/best',  # Ensure best audio format
        'noplaylist': True,  # Avoid downloading playlists
    }

    # Configure audio-specific options
    if request.media_type == "audio":
        if request.bitrate:
            ydl_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': request.bitrate,
                }
            ]

    # Enable debug logging for yt-dlp
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    ydl_opts['logger'] = logger

    try:
        # First download attempt to get original title and file info
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(request.url, download=True)

        # Extract the original title and sanitize it
        original_title = info_dict['title']
        print(f"Original title: {original_title}")

        # Sanitize the filename to remove invalid characters
        sanitized_title = sanitize_filename(original_title)
        print(f"Sanitized title: {sanitized_title}")

        # Find the downloaded file using the unique video ID (since the output is based on the ID)
        downloaded_file_path = f"downloads/{info_dict['id']}.mp3"
        if not os.path.exists(downloaded_file_path):
            return {"error": f"Downloaded file not found for {original_title}"}

        print(f"Actual downloaded file path: {downloaded_file_path}")

        # Rename the downloaded file to the sanitized title
        sanitized_file_path = f"downloads/{sanitized_title}.mp3"
        os.rename(downloaded_file_path, sanitized_file_path)
        print(f"Renamed file to: {sanitized_file_path}")

        # Get thumbnail URL from the video info
        thumbnail_url = info_dict.get('thumbnail', None)
        if thumbnail_url:
            # Download the thumbnail
            print(f"Found thumbnail URL: {thumbnail_url}")
            thumbnail_response = requests.get(thumbnail_url)
            thumbnail_path = f"downloads/{sanitized_title}_thumbnail.jpg"
            with open(thumbnail_path, 'wb') as f:
                f.write(thumbnail_response.content)

            # Temporary file for FFmpeg output
            temp_mp3_file_path = f"downloads/{sanitized_title}_temp.mp3"

            # Embed the thumbnail into the MP3 file using FFmpeg
            if os.path.exists(sanitized_file_path):
                subprocess.run([
                    'ffmpeg',
                    '-i', sanitized_file_path,  # Input MP3 file
                    '-i', thumbnail_path,  # Thumbnail image
                    '-map', '0',  # Map the audio stream
                    '-map', '1',  # Map the image
                    '-c:v', 'mjpeg',  # Use JPEG format for the image
                    '-metadata', f"title={original_title}",
                    '-metadata', f"artist={info_dict.get('uploader', 'Unknown')}",
                    '-id3v2_version', '3',  # Use ID3v2 tags
                    '-y',  # Overwrite the output file
                    temp_mp3_file_path  # Output file
                ], check=True)

                # Replace the original file with the updated file
                shutil.move(temp_mp3_file_path, sanitized_file_path)

            # Clean up the thumbnail image
            os.remove(thumbnail_path)
        else:
            print("No thumbnail found for the video.")

        background_tasks.add_task(delete_file, sanitized_file_path)

        if not os.path.exists(sanitized_file_path):
            print(f"File not found at: {sanitized_file_path}")
            return {"error": "File not found."}

        url_encoded_title = quote(sanitized_title)  # URL encode for HTTP

        print(f"Serving file: {sanitized_file_path}")
        return FileResponse(
            sanitized_file_path,
            media_type="audio/mpeg",
            filename=f"{url_encoded_title}.mp3",
            headers={"Content-Disposition": f'attachment; filename="{url_encoded_title}.mp3"'}
        )

    except Exception as e:
        return {"error": str(e)}
