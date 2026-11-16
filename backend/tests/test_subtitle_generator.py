import pytest
from pathlib import Path
from app.services.subtitle_generator import (
    generate_ass_subtitle_file,
    format_ass_timestamp,
    THEME_STYLES
)

def test_format_ass_timestamp():
    assert format_ass_timestamp(0.0) == "0:00:00.00"
    assert format_ass_timestamp(65.45) == "0:01:05.45"
    assert format_ass_timestamp(3661.12) == "1:01:01.12"

def test_generate_ass_subtitle_file(tmp_path: Path):
    segments = [
        {
            "start": 5.0,
            "end": 9.5,
            "text": "This is a viral hook test",
            "words": [
                {"word": "This", "start": 5.0, "end": 5.5},
                {"word": "is", "start": 5.5, "end": 6.0},
                {"word": "a", "start": 6.0, "end": 6.5},
                {"word": "viral", "start": 6.5, "end": 7.5},
                {"word": "hook", "start": 7.5, "end": 8.5},
                {"word": "test", "start": 8.5, "end": 9.5},
            ]
        },
        {
            "start": 10.0,
            "end": 14.0,
            "text": "Second sentence that follows",
            "words": []
        }
    ]
    out_file = tmp_path / "test.ass"
    
    # Test karaoke style with anime theme
    generate_ass_subtitle_file(
        segments=segments,
        output_path=out_file,
        clip_start=5.0,
        clip_end=15.0,
        theme="anime",
        caption_style="karaoke"
    )

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "[V4+ Styles]" in content
    assert "Arial Black" in content
    assert r"{\k50}This" in content
    # First segment rel start should be 0:00:00.00
    assert "Dialogue: 0,0:00:00.00,0:00:04.50" in content

def test_generate_ass_sentence_style(tmp_path: Path):
    segments = [
        {"start": 1.0, "end": 3.0, "text": "Clean sentence without karaoke"}
    ]
    out_file = tmp_path / "sentence.ass"
    generate_ass_subtitle_file(
        segments=segments,
        output_path=out_file,
        clip_start=0.0,
        clip_end=5.0,
        theme="blueprint",
        caption_style="sentence"
    )
    content = out_file.read_text(encoding="utf-8")
    assert "Courier New" in content
    assert "Clean sentence without karaoke" in content
    assert r"{\k" not in content
