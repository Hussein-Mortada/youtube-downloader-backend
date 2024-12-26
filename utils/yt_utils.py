from yt_dlp import YoutubeDL

def fetch_metadata(url):
    ydl_opts = {"quiet": True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_file(url, format_id, output_dir="downloads"):
    ydl_opts = {
        "format": format_id,
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
