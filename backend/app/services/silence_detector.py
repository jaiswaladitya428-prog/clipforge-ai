import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from .ffmpeg_utils import get_ffmpeg_binary

def detect_silence(audio_or_video_path: Path, noise_db: int = -30, min_duration: float = 0.5) -> List[Dict[str, Any]]:
    """
    Detect silence intervals using FFmpeg's silencedetect filter.
    Returns list of {"start": float, "end": float, "duration": float}.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [
        ffmpeg_exe,
        "-i", str(audio_or_video_path),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    stderr = result.stderr

    silences: List[Dict[str, Any]] = []
    current_start = None

    for line in stderr.splitlines():
        if "silence_start:" in line:
            match = re.search(r"silence_start:\s*([\d\.]+)", line)
            if match:
                current_start = float(match.group(1))
        elif "silence_end:" in line:
            match_end = re.search(r"silence_end:\s*([\d\.]+)", line)
            match_dur = re.search(r"silence_duration:\s*([\d\.]+)", line)
            if match_end and current_start is not None:
                end_time = float(match_end.group(1))
                duration = float(match_dur.group(1)) if match_dur else round(end_time - current_start, 2)
                silences.append({
                    "start": round(current_start, 2),
                    "end": round(end_time, 2),
                    "duration": round(duration, 2)
                })
                current_start = None

    return silences
