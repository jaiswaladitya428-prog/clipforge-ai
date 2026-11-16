import subprocess
from pathlib import Path
from app.services.ffmpeg_utils import get_ffmpeg_binary
from app.services.silence_detector import detect_silence
from app.services.scene_detector import detect_scenes
from app.services.frame_extractor import extract_representative_frames

def create_sample_video(output_path: Path):
    ffmpeg_exe = get_ffmpeg_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Generate 3-second video with 1 second tone, 1 second silence, 1 second tone
    cmd = [
        ffmpeg_exe,
        "-f", "lavfi", "-i", "testsrc=duration=3:size=320x240:rate=15",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-f", "lavfi", "-i", "aevalsrc=0:duration=1",
        "-f", "lavfi", "-i", "sine=frequency=880:duration=1",
        "-filter_complex", "[1:a][2:a][3:a]concat=n=3:v=0:a=1[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le",
        "-y", str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def test_silence_detection(tmp_path):
    video = create_sample_video(tmp_path / "silence_test.mp4")
    assert video.exists()

    silences = detect_silence(video, noise_db=-30, min_duration=0.5)
    # Should detect the 1-second silence interval between sec 1 and 2
    assert isinstance(silences, list)
    assert len(silences) >= 1
    assert any(s["duration"] >= 0.5 for s in silences)

def test_scene_detection_and_frames(tmp_path):
    video = create_sample_video(tmp_path / "scenes_test.mp4")
    scenes = detect_scenes(video, video_duration=3.0)
    assert len(scenes) >= 1
    assert scenes[0]["start_time"] == 0.0

    frames_dir = tmp_path / "frames"
    frames = extract_representative_frames(video, scenes, frames_dir)
    assert len(frames) >= 1
    assert (frames_dir / frames[0]["filename"]).exists()
