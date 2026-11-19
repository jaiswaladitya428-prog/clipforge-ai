import pytest
from app.services.gemini_service import score_sliding_30s_windows, score_30s_window

def test_score_30s_window_high_viral():
    # Window with hook question, rapid start, and high speech density
    words = [
        {"word": "Why", "start": 0.2, "end": 0.6},
        {"word": "is", "start": 0.6, "end": 0.8},
        {"word": "everyone", "start": 0.8, "end": 1.4},
        {"word": "talking", "start": 1.4, "end": 1.8},
        {"word": "about", "start": 1.8, "end": 2.1},
        {"word": "this", "start": 2.1, "end": 2.3},
        {"word": "secret?", "start": 2.3, "end": 2.8},
    ]
    # Add filler punchy words to reach optimal pacing
    for i in range(70):
        t = 3.0 + i * 0.35
        words.append({"word": f"keypoint{i}", "start": round(t, 2), "end": round(t + 0.3, 2)})
    # Final word with clean payoff
    words.append({"word": "proven!", "start": 28.5, "end": 29.2})

    score = score_30s_window(words, start_t=0.0, end_t=30.0)
    assert score >= 95, f"Expected viral score >= 95 for explosive hook window, got {score}"

def test_score_sliding_30s_windows_filtration_and_nms():
    # 2-minute video with a standout high-virality 30s window at 30s
    segments = []
    # 0s - 30s: slow speech
    segments.append({
        "start": 0.0,
        "end": 28.0,
        "text": "Hello today we are just going to chat calmly about nothing special.",
        "words": [{"word": "Hello", "start": 1.0, "end": 2.0}]
    })
    # 30s - 60s: explosive viral hook
    viral_words = [
        {"word": "Why", "start": 30.2, "end": 30.6},
        {"word": "did", "start": 30.6, "end": 30.8},
        {"word": "nobody", "start": 30.8, "end": 31.4},
        {"word": "reveal", "start": 31.4, "end": 31.8},
        {"word": "this", "start": 31.8, "end": 32.1},
        {"word": "secret?", "start": 32.1, "end": 32.8},
    ]
    for i in range(75):
        t = 33.0 + i * 0.33
        viral_words.append({"word": f"insight{i}", "start": round(t, 2), "end": round(t + 0.3, 2)})
    viral_words.append({"word": "truth.", "start": 58.5, "end": 59.2})

    segments.append({
        "start": 30.0,
        "end": 60.0,
        "text": "Why did nobody reveal this secret? ...",
        "words": viral_words
    })

    # 60s - 120s: calm outro
    segments.append({
        "start": 60.0,
        "end": 120.0,
        "text": "Thank you for listening to this presentation.",
        "words": [{"word": "Thank", "start": 62.0, "end": 63.0}]
    })

    clips = score_sliding_30s_windows(segments, video_duration=120.0, window_size=30.0, step=5.0, min_score=95)
    assert len(clips) >= 1, "Expected at least 1 clip scoring >= 95"
    top_clip = clips[0]
    assert top_clip["viral_score"] >= 95
    assert abs(top_clip["start_time"] - 30.0) <= 5.0, f"Expected start time near 30s, got {top_clip['start_time']}"
    assert top_clip["end_time"] > top_clip["start_time"]
