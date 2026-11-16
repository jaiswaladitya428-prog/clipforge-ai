import subprocess
from pathlib import Path
import pytest
from app.services.ffmpeg_utils import get_ffmpeg_binary
from app.services.video_renderer import render_styled_video
from app.services.subtitle_generator import generate_ass_subtitle_file

def test_render_styled_video_integration(tmp_path: Path):
    ffmpeg_exe = get_ffmpeg_binary()
    input_video = tmp_path / "synthetic_input.mp4"
    output_video = tmp_path / "rendered_9_16.mp4"
    sub_path = tmp_path / "sub.ass"

    # 1. Create a 3-second synthetic test video with audio
    create_cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "testsrc=duration=3:size=640x360:rate=24",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "3",
        "-c:v", "libx264", "-c:a", "aac",
        str(input_video)
    ]
    res = subprocess.run(create_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0
    assert input_video.exists()

    # 2. Create sample subtitles
    segments = [
        {"start": 0.5, "end": 2.5, "text": "Viral Short Clip Test"}
    ]
    generate_ass_subtitle_file(
        segments=segments,
        output_path=sub_path,
        clip_start=0.0,
        clip_end=3.0,
        theme="anime",
        caption_style="karaoke"
    )
    assert sub_path.exists()

    # 3. Render styled 9:16 video
    rendered = render_styled_video(
        input_video_path=input_video,
        output_video_path=output_video,
        start_time=0.5,
        end_time=2.5,
        aspect_ratio="9:16",
        theme="anime",
        subtitle_ass_path=sub_path
    )

    assert rendered.exists()
    assert rendered.stat().st_size > 1000  # Non-trivial MP4 file
