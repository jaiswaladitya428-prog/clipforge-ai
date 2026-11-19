import pytest
from app.services.youtube_downloader import validate_youtube_url
from app.services.gemini_service import extract_viral_highlights

def test_validate_youtube_url_formats():
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "https://youtube.com/live/abcdef12345?feature=share",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    ]
    for url in valid_urls:
        assert validate_youtube_url(url) is True, f"Failed for {url}"

    invalid_urls = [
        "https://vimeo.com/123456",
        "https://tiktok.com/@user/video/123",
        "not a url",
        "",
        "https://google.com",
    ]
    for url in invalid_urls:
        assert validate_youtube_url(url) is False, f"Should be invalid: {url}"

def test_multi_clip_heuristic_extraction():
    # Synthetic 3-minute transcript with several speech segments
    segments = []
    for minute in range(3):
        for sec in range(0, 60, 5):
            t = minute * 60 + sec
            segments.append({
                "start": float(t),
                "end": float(t + 4.5),
                "text": f"Here is high energy speech segment at {t} seconds talking about viral video tips and strategies."
            })

    # Request multi-clip extraction
    clips = extract_viral_highlights(segments, video_duration=180.0, api_key="", target_count=4)
    
    assert len(clips) >= 3, f"Expected at least 3 clips, got {len(clips)}"
    for i, clip in enumerate(clips):
        assert "start_time" in clip
        assert "end_time" in clip
        assert "hook_title" in clip
        assert clip["viral_score"] >= 75
        dur = clip["end_time"] - clip["start_time"]
        assert dur > 0, f"Clip {i} duration must be positive"
        assert dur <= 180.0, f"Clip {i} duration cannot exceed video duration"

def test_yt_dlp_ffmpeg_integration():
    import yt_dlp
    from app.services.ffmpeg_utils import get_ffmpeg_binary
    exe = get_ffmpeg_binary()
    assert exe is not None
    # Verify yt-dlp identifies FFmpeg as available for multi-format merging
    ydl = yt_dlp.YoutubeDL({"ffmpeg_location": exe})
    pp = yt_dlp.postprocessor.ffmpeg.FFmpegPostProcessor(ydl)
    assert pp.available is True, "FFmpeg must be detected as available by yt-dlp"
