import logging
import subprocess
from pathlib import Path
from typing import Optional
from .ffmpeg_utils import get_ffmpeg_binary

logger = logging.getLogger(__name__)

THEME_COLOR_FILTERS = {
    "anime": "eq=saturation=1.5:contrast=1.2:brightness=0.02",
    "blueprint": "colorbalance=bs=0.4:bm=0.3:bh=0.2:rs=-0.3:rm=-0.2:rh=-0.2,eq=contrast=1.2:saturation=1.3",
    "ghibli": "colorbalance=rs=0.2:gs=0.1:bs=-0.2:rm=0.15:gm=0.08:bm=-0.15,eq=contrast=1.1:saturation=1.15",
    "papercut": "eq=contrast=1.2:saturation=0.85:brightness=0.02",
    "minimal": "eq=contrast=1.08:saturation=1.05",
}

def escape_ffmpeg_path(path: Path) -> str:
    """Escape file path for FFmpeg filter arguments on Windows."""
    posix_path = path.as_posix()
    # On Windows, escape colon in drive letter (e.g. C: -> C\\:)
    escaped = posix_path.replace(":", r"\:")
    return escaped

def render_styled_video(
    input_video_path: Path,
    output_video_path: Path,
    start_time: float,
    end_time: float,
    aspect_ratio: str = "9:16",
    theme: str = "minimal",
    subtitle_ass_path: Optional[Path] = None
) -> Path:
    """
    Renders trimmed and styled video with aspect ratio transformation,
    theme color grading, and burned-in ASS subtitles using native FFmpeg.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    clip_duration = max(1.0, end_time - start_time)
    theme_key = theme.lower() if theme.lower() in THEME_COLOR_FILTERS else "minimal"
    color_filter = THEME_COLOR_FILTERS[theme_key]

    filter_complex_parts = []

    if aspect_ratio == "9:16":
        # 9:16 Vertical Shorts (1080x1920) with blurred background stack
        filter_complex_parts.append(
            "[0:v]split=2[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bgblur];"
            "[fg]scale=1080:-2[fgscaled];"
            "[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2[base]"
        )
    else:
        # 16:9 Landscape (1920x1080)
        filter_complex_parts.append(
            "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[base]"
        )

    # Apply Theme Color Filter
    filter_complex_parts.append(f"[base]{color_filter}[colored]")
    last_v_tag = "[colored]"

    # Apply Subtitles if ASS file provided
    if subtitle_ass_path and subtitle_ass_path.exists():
        escaped_sub_path = escape_ffmpeg_path(subtitle_ass_path)
        filter_complex_parts.append(f"{last_v_tag}subtitles='{escaped_sub_path}'[outv]")
        last_v_tag = "[outv]"

    full_filter_complex = ";".join(filter_complex_parts)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", str(round(start_time, 3)),
        "-to", str(round(end_time, 3)),
        "-i", str(input_video_path),
        "-filter_complex", full_filter_complex,
        "-map", last_v_tag,
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_video_path)
    ]

    logger.info(f"Running FFmpeg render: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="ignore"
    )

    if result.returncode != 0:
        logger.error(f"FFmpeg render failed with error: {result.stderr}")
        raise RuntimeError(f"FFmpeg render failed (code {result.returncode}): {result.stderr[-400:]}")

    if not output_video_path.exists() or output_video_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg completed but output video file was not created or is empty.")

    return output_video_path
