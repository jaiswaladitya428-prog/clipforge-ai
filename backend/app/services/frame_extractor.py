import subprocess
from pathlib import Path
from typing import List, Dict, Any
from .ffmpeg_utils import get_ffmpeg_binary

def extract_representative_frames(
    video_path: Path,
    scenes: List[Dict[str, Any]],
    output_dir: Path
) -> List[Dict[str, Any]]:
    """
    Extract representative keyframe thumbnails for each detected scene.
    Saves JPG images into output_dir and returns metadata with filenames and timestamps.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_frames: List[Dict[str, Any]] = []

    for scene in scenes:
        scene_num = scene.get("scene_number", 1)
        start = scene.get("start_time", 0.0)
        end = scene.get("end_time", start + 2.0)
        # Capture frame at middle of scene
        capture_time = round((start + end) / 2.0, 2)
        filename = f"scene_{scene_num}_{int(capture_time*100)}ms.jpg"
        frame_path = output_dir / filename

        cmd = [
            ffmpeg_exe,
            "-ss", str(capture_time),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            "-y", str(frame_path)
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if frame_path.exists():
            extracted_frames.append({
                "scene_number": scene_num,
                "timestamp": capture_time,
                "filename": filename
            })

    # If no frames could be extracted from scenes, take a fallback thumbnail at 00:00:01
    if not extracted_frames:
        fallback_file = "thumbnail.jpg"
        fallback_path = output_dir / fallback_file
        subprocess.run([
            ffmpeg_exe, "-ss", "0.5", "-i", str(video_path),
            "-vframes", "1", "-q:v", "2", "-y", str(fallback_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if fallback_path.exists():
            extracted_frames.append({
                "scene_number": 1,
                "timestamp": 0.5,
                "filename": fallback_file
            })

    return extracted_frames
