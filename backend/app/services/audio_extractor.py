import subprocess
from pathlib import Path
from .ffmpeg_utils import get_ffmpeg_binary, has_audio_stream, extract_video_metadata

def extract_audio_wav(video_path: Path, output_wav_path: Path) -> Path:
    """
    Extract 16kHz mono WAV from video for optimal faster-whisper transcription.
    If the video has no audio track (e.g. YouTube DASH video-only stream or muted file),
    generates a silent audio track so downstream processing continues gracefully without crashing.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    if not has_audio_stream(video_path):
        duration, _, _ = extract_video_metadata(video_path)
        dur = min(duration if duration and duration > 0 else 5.0, 60.0)
        cmd = [
            ffmpeg_exe,
            "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=16000:cl=mono",
            "-t", str(dur),
            "-acodec", "pcm_s16le",
            str(output_wav_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        if result.returncode != 0:
            raise RuntimeError(f"Silent audio generation failed: {result.stderr}")
        return output_wav_path

    cmd = [
        ffmpeg_exe,
        "-i", str(video_path),
        "-vn",                   # No video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",          # 16kHz sample rate
        "-ac", "1",              # Mono channel
        "-y",                    # Overwrite
        str(output_wav_path)
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr}")
        
    return output_wav_path
