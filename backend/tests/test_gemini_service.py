from app.services.gemini_service import extract_viral_highlights, _fallback_heuristic_clips

def test_gemini_heuristic_fallback():
    segments = [
        {"start": 0.0, "end": 10.0, "text": "Intro talking slow"},
        {"start": 10.0, "end": 20.0, "text": "Now here is the main explosive point that everyone was waiting to hear about right now"},
        {"start": 20.0, "end": 35.0, "text": "And this is why viral hooks matter for your videos every single day without exception"},
        {"start": 35.0, "end": 45.0, "text": "Follow for more tips and subscribe"},
    ]
    clips = extract_viral_highlights(segments, video_duration=45.0, api_key="")
    assert len(clips) >= 1
    clip = clips[0]
    assert "start_time" in clip
    assert "end_time" in clip
    assert clip["end_time"] > clip["start_time"]
    assert clip["viral_score"] >= 80
    assert "hook_title" in clip
