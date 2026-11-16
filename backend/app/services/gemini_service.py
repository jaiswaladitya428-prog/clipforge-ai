import json
import logging
import re
from typing import List, Dict, Any, Optional
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def _format_transcript_for_prompt(segments: List[Dict[str, Any]]) -> str:
    lines = []
    for s in segments:
        start = round(float(s.get("start", 0)), 2)
        end = round(float(s.get("end", 0)), 2)
        text = s.get("text", "").strip()
        lines.append(f"[{start}s - {end}s] {text}")
    return "\n".join(lines)

def _fallback_heuristic_clips(segments: List[Dict[str, Any]], video_duration: float = 0.0) -> List[Dict[str, Any]]:
    """Heuristic fallback to pick the most speech-dense 30-50s clip if Gemini is unavailable."""
    if not segments:
        clip_end = min(30.0, video_duration if video_duration > 0 else 30.0)
        return [{
            "start_time": 0.0,
            "end_time": clip_end,
            "hook_title": "Top Clip Highlight",
            "viral_score": 85,
            "reasoning": "Selected opening segment with high initial pacing.",
            "suggested_theme": "minimal",
            "suggested_caption_style": "karaoke"
        }]

    # Find the 35-45s window with highest word/character density
    total_duration = max(segments[-1].get("end", 0.0), video_duration)
    target_len = min(40.0, max(25.0, total_duration))
    
    best_start = float(segments[0].get("start", 0.0))
    best_end = min(best_start + target_len, total_duration)
    best_density = 0

    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0.0))
        end_target = start + target_len
        if end_target > total_duration + 5.0 and i > 0:
            break
        
        # Count words in this window
        words_in_window = 0
        actual_end = start
        for next_seg in segments[i:]:
            seg_start = float(next_seg.get("start", 0.0))
            seg_end = float(next_seg.get("end", 0.0))
            if seg_start > end_target:
                break
            actual_end = seg_end
            words_in_window += len(next_seg.get("text", "").split())
        
        if words_in_window > best_density and (actual_end - start) >= 20.0:
            best_density = words_in_window
            best_start = start
            best_end = min(actual_end, start + 60.0)

    first_text = segments[0].get("text", "").strip()
    preview_title = (first_text[:40] + "...") if len(first_text) > 40 else (first_text or "Top Highlight Clip")

    return [{
        "start_time": round(best_start, 2),
        "end_time": round(best_end, 2),
        "hook_title": preview_title,
        "viral_score": 88,
        "reasoning": "Highest speech density and momentum segment.",
        "suggested_theme": "anime",
        "suggested_caption_style": "karaoke"
    }]

def extract_viral_highlights(
    segments: List[Dict[str, Any]],
    video_duration: float = 0.0,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes transcript with Google Gemini to identify the most viral 30-60s clip(s).
    Falls back to speech-density heuristic if API key is not provided or network fails.
    """
    key = api_key or settings.GEMINI_API_KEY
    if not key or not segments:
        logger.info("Using heuristic highlight fallback (no Gemini API key or empty segments).")
        return _fallback_heuristic_clips(segments, video_duration)

    formatted_transcript = _format_transcript_for_prompt(segments)
    
    prompt = f"""You are a master viral video editor specializing in YouTube Shorts, TikTok, and Instagram Reels.
Analyze this timestamped speech transcript from a video. Identify the TOP 1 to 3 most viral, engaging segments (each strictly between 25 and 60 seconds long).
Look for:
- A strong opening hook statement or provocative question
- High emotional momentum, surprising revelation, or punchy storytelling
- A clear conclusion or cliffhanger

Transcript:
{formatted_transcript}

Respond ONLY with a JSON object strictly adhering to this format:
{{
  "viral_clips": [
    {{
      "start_time": float (seconds, e.g. 15.2),
      "end_time": float (seconds, e.g. 52.8),
      "hook_title": "Catchy headline for the short",
      "viral_score": int (1 to 100),
      "reasoning": "Brief explanation of why this hook retains viewers",
      "suggested_theme": "blueprint" | "anime" | "ghibli" | "papercut" | "minimal",
      "suggested_caption_style": "karaoke" | "sentence"
    }}
  ]
}}"""

    try:
        url = f"{GEMINI_API_URL}?key={key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json"
            }
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Clean any accidental markdown code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        
        parsed = json.loads(cleaned)
        clips = parsed.get("viral_clips", [])
        
        if not clips:
            return _fallback_heuristic_clips(segments, video_duration)

        # Validate and clamp timestamps
        validated_clips = []
        for c in clips:
            s_time = max(0.0, float(c.get("start_time", 0.0)))
            e_time = float(c.get("end_time", s_time + 30.0))
            if video_duration > 0:
                e_time = min(video_duration, e_time)
            
            # Ensure clip length is between 15 and 65 seconds
            if e_time - s_time < 15.0:
                e_time = min(s_time + 35.0, video_duration if video_duration > 0 else s_time + 35.0)

            validated_clips.append({
                "start_time": round(s_time, 2),
                "end_time": round(e_time, 2),
                "hook_title": str(c.get("hook_title", "Viral Highlight")),
                "viral_score": int(c.get("viral_score", 90)),
                "reasoning": str(c.get("reasoning", "Strong retention potential")),
                "suggested_theme": str(c.get("suggested_theme", "minimal")).lower(),
                "suggested_caption_style": str(c.get("suggested_caption_style", "karaoke")).lower()
            })

        return validated_clips or _fallback_heuristic_clips(segments, video_duration)

    except Exception as e:
        logger.warning(f"Gemini API request failed, falling back to heuristic: {e}")
        return _fallback_heuristic_clips(segments, video_duration)
