import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from .ffmpeg_utils import get_ffmpeg_binary

def detect_scenes(video_path: Path, video_duration: float = 0.0, threshold: float = 0.3) -> List[Dict[str, Any]]:
    """
    Detect visual scene changes using FFmpeg's scene score filter.
    Returns list of scenes: [{"scene_number": int, "start_time": float, "end_time": float}].
    """
    ffmpeg_exe = get_ffmpeg_binary()
    cmd = [
        ffmpeg_exe,
        "-i", str(video_path),
        "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    stderr = result.stderr

    change_timestamps: List[float] = [0.0]

    for line in stderr.splitlines():
        if "showinfo" in line and "pts_time:" in line:
            match = re.search(r"pts_time:\s*([\d\.]+)", line)
            if match:
                ts = float(match.group(1))
                # Avoid duplicate cuts within 0.5s
                if ts - change_timestamps[-1] > 0.5:
                    change_timestamps.append(round(ts, 2))

    if video_duration > 0 and (video_duration - change_timestamps[-1]) > 0.5:
        change_timestamps.append(round(video_duration, 2))
    elif len(change_timestamps) == 1:
        change_timestamps.append(round(video_duration, 2) if video_duration > 0 else 10.0)

    # Convert timestamps to scene intervals
    scenes: List[Dict[str, Any]] = []
    for i in range(len(change_timestamps) - 1):
        start = change_timestamps[i]
        end = change_timestamps[i + 1]
        scenes.append({
            "scene_number": i + 1,
            "start_time": start,
            "end_time": end,
            "duration": round(end - start, 2)
        })

    return scenes
