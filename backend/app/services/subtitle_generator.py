from pathlib import Path
from typing import List, Dict, Any, Optional

THEME_STYLES = {
    "minimal": {
        "fontname": "Arial",
        "fontsize": 48,
        "primary_color": "&H00FFFFFF&",     # White (BGR)
        "secondary_color": "&H0000FFFF&",   # Yellow active
        "outline_color": "&H00111111&",     # Deep black/charcoal
        "back_color": "&H80000000&",        # 50% translucent black
        "bold": 1,
        "outline": 3,
        "shadow": 1,
        "alignment": 2,                     # Bottom Center
        "margin_v": 120,
    },
    "blueprint": {
        "fontname": "Courier New",
        "fontsize": 44,
        "primary_color": "&H00FFE500&",     # Cyan
        "secondary_color": "&H00FFFFFF&",   # White
        "outline_color": "&H0032140A&",     # Deep navy
        "back_color": "&HA0001020&",
        "bold": 1,
        "outline": 2,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 130,
    },
    "anime": {
        "fontname": "Arial Black",
        "fontsize": 54,
        "primary_color": "&H0000FFFF&",     # Neon Yellow
        "secondary_color": "&H00FF00FF&",   # Magenta
        "outline_color": "&H00000000&",     # Black outline
        "back_color": "&H60FF0080&",
        "bold": 1,
        "outline": 4,
        "shadow": 3,
        "alignment": 2,
        "margin_v": 140,
    },
    "ghibli": {
        "fontname": "Trebuchet MS",
        "fontsize": 46,
        "primary_color": "&H00E7F8FF&",     # Warm cream
        "secondary_color": "&H004AA5FF&",   # Golden orange
        "outline_color": "&H001B2E3D&",     # Warm dark earth
        "back_color": "&H70000000&",
        "bold": 1,
        "outline": 2.5,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 120,
    },
    "papercut": {
        "fontname": "Trebuchet MS",
        "fontsize": 48,
        "primary_color": "&H00FFFFFF&",
        "secondary_color": "&H0022C55E&",   # Soft green
        "outline_color": "&H0018181B&",     # Zinc dark
        "back_color": "&HB0000000&",
        "bold": 1,
        "outline": 3,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 130,
    }
}

def format_ass_timestamp(seconds: float) -> str:
    """Format seconds into ASS timestamp H:MM:SS.cs"""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def generate_ass_subtitle_file(
    segments: List[Dict[str, Any]],
    output_path: Path,
    clip_start: float = 0.0,
    clip_end: Optional[float] = None,
    theme: str = "minimal",
    caption_style: str = "karaoke",
    target_width: int = 1080,
    target_height: int = 1920
) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file formatted for the chosen theme and caption style.
    Timestamps are adjusted relative to clip_start.
    """
    theme_key = theme.lower() if theme.lower() in THEME_STYLES else "minimal"
    style_cfg = THEME_STYLES[theme_key]

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {target_width}
PlayResY: {target_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_cfg['fontname']},{style_cfg['fontsize']},{style_cfg['primary_color']},{style_cfg['secondary_color']},{style_cfg['outline_color']},{style_cfg['back_color']},{style_cfg['bold']},0,0,0,100,100,0,0,1,{style_cfg['outline']},{style_cfg['shadow']},{style_cfg['alignment']},40,40,{style_cfg['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    for seg in segments:
        seg_start = float(seg.get("start", 0.0))
        seg_end = float(seg.get("end", 0.0))
        text = seg.get("text", "").strip()

        # Check if segment overlaps with the clipped timeframe
        if clip_end is not None and seg_start >= clip_end:
            continue
        if seg_end <= clip_start:
            continue

        # Adjust timestamps relative to clip_start
        rel_start = max(0.0, seg_start - clip_start)
        rel_end = (seg_end - clip_start) if clip_end is None else min(seg_end - clip_start, clip_end - clip_start)

        if rel_end <= rel_start or not text:
            continue

        start_str = format_ass_timestamp(rel_start)
        end_str = format_ass_timestamp(rel_end)

        words = seg.get("words", [])
        
        # Word-by-word karaoke style if words with timestamps exist
        if caption_style == "karaoke" and words:
            karaoke_parts = []
            for w in words:
                w_start = float(w.get("start", seg_start))
                w_end = float(w.get("end", seg_end))
                w_dur_cs = max(10, int(round((w_end - w_start) * 100)))
                word_text = w.get("word", "").strip()
                if word_text:
                    karaoke_parts.append(f"{{\\k{w_dur_cs}}}{word_text}")
            
            line_text = " ".join(karaoke_parts) if karaoke_parts else text
        else:
            # Clean sentence / phrase card style
            line_text = text

        # Clean backslashes/newlines in text
        clean_text = line_text.replace("\n", " ").replace("\\N", " ").strip()
        dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{clean_text}")

    content = header + "\n".join(dialogue_lines) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
