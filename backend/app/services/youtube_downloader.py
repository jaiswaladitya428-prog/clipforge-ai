import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional
import yt_dlp
from .ffmpeg_utils import get_ffmpeg_binary

logger = logging.getLogger(__name__)

YOUTUBE_URL_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|live/|shorts/|embed/)|youtu\.be/)[\w\-]+.*$",
    re.IGNORECASE
)

def validate_youtube_url(url: str) -> bool:
    """Validate whether a string is a valid YouTube video or live URL."""
    if not url or not isinstance(url, str):
        return False
    return bool(YOUTUBE_URL_REGEX.match(url.strip()))

def get_youtube_info(url: str) -> Dict[str, Any]:
    """Extract metadata (title, duration, thumbnail) without downloading."""
    if not validate_youtube_url(url):
        raise ValueError(f"Invalid YouTube URL format: {url}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url.strip(), download=False)
        return {
            "title": info.get("title", "YouTube Video"),
            "duration": info.get("duration", 0.0),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader", "Unknown Creator"),
            "is_live": info.get("is_live", False),
        }

def download_youtube_video(url: str, output_path: Path, max_duration_seconds: int = 3600) -> Dict[str, Any]:
    """
    Downloads YouTube video or livestream VOD, muxing best 1080p/720p video + audio
    using local embedded FFmpeg binary into a single MP4 file.
    """
    if not validate_youtube_url(url):
        raise ValueError(f"Invalid YouTube URL format: {url}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = get_ffmpeg_binary()

    # Base filename without extension for yt-dlp outtmpl
    out_stem = output_path.with_suffix("")
    
    ydl_opts = {
        # Best video (up to 1080p) + best audio, fallback to best standard mp4
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best",
        "outtmpl": f"{out_stem}.%(ext)s",
        "ffmpeg_location": ffmpeg_exe,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "live_from_start": True,  # For live VODs
    }

    logger.info(f"Downloading YouTube video from {url} to {output_path}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url.strip(), download=True)
        duration = float(info.get("duration", 0.0) or 0.0)

        # Look for the merged/final MP4 file produced by yt-dlp
        expected_mp4 = output_path.with_suffix(".mp4")
        if not expected_mp4.exists():
            # If yt-dlp saved directly to outtmpl or another extension
            candidates = list(output_path.parent.glob(f"{output_path.stem}*"))
            if candidates:
                expected_mp4 = candidates[0]
            else:
                raise RuntimeError("yt-dlp completed download but output file was not found on disk.")

        # Ensure filename matches expected output_path exactly
        if expected_mp4 != output_path:
            expected_mp4.replace(output_path)

        return {
            "title": info.get("title", "YouTube Video"),
            "duration": duration,
            "uploader": info.get("uploader", "YouTube Creator"),
            "thumbnail": info.get("thumbnail"),
            "file_path": output_path,
            "file_size": output_path.stat().st_size if output_path.exists() else 0,
            "is_live": info.get("is_live", False),
        }
