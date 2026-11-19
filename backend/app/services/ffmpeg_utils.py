import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

def get_ffmpeg_binary() -> str:
    """
    Return path to ffmpeg executable, preferring imageio-ffmpeg for reliability on Windows.
    Ensures a standardized 'ffmpeg.exe' binary exists and is available on os.environ['PATH'].
    """
    try:
        import imageio_ffmpeg
        raw_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if raw_exe and Path(raw_exe).exists():
            raw_path = Path(raw_exe)
            bin_dir = raw_path.parent
            std_exe = bin_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if not std_exe.exists():
                try:
                    os.link(str(raw_path), str(std_exe))
                except Exception:
                    try:
                        shutil.copy2(str(raw_path), str(std_exe))
                    except Exception:
                        pass
            
            final_exe = str(std_exe) if std_exe.exists() else str(raw_path)
            
            # Ensure bin_dir is in os.environ['PATH'] so yt-dlp & child processes find it automatically
            if str(bin_dir) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
                
            return final_exe
    except ImportError:
        pass
    
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
        
    raise RuntimeError("FFmpeg executable could not be found via imageio-ffmpeg or system PATH.")

def extract_video_metadata(video_path: Path) -> Tuple[Optional[float], Optional[int], Optional[int]]:
    """Extract duration, width, height from video using ffprobe or ffmpeg info."""
    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [ffmpeg_exe, "-i", str(video_path)]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
    output = result.stderr
    
    duration = None
    width = None
    height = None

    # Parse Duration: 00:01:23.45
    import re
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d\.]+)", output)
    if dur_match:
        hours, minutes, seconds = dur_match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    # Parse resolution e.g., 1920x1080 or 1080x1920
    res_match = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", output)
    if res_match:
        width = int(res_match.group(1))
        height = int(res_match.group(2))

    return duration, width, height

def has_audio_stream(video_path: Path) -> bool:
    """Check if the video file contains an audio stream."""
    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [ffmpeg_exe, "-i", str(video_path)]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
    return "Audio:" in result.stderr
