import json
from pathlib import Path
from typing import Dict, Any
from ..core.config import settings

_model = None

def get_whisper_model():
    """Lazy-load the faster-whisper model to keep memory footprint light."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        # Use INT8 and CPU by default to keep memory under 350MB
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE
        )
    return _model

def transcribe_audio_file(audio_path: Path) -> Dict[str, Any]:
    """
    Transcribe audio with word-level and segment-level timestamps.
    Returns structured dict with language, duration, and segments.
    """
    model = get_whisper_model()
    segments_generator, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        word_timestamps=True
    )

    segments_list = []
    for segment in segments_generator:
        seg_data = {
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "words": []
        }
        if segment.words:
            for word in segment.words:
                seg_data["words"].append({
                    "word": word.word.strip(),
                    "start": round(word.start, 2),
                    "end": round(word.end, 2),
                    "probability": round(word.probability, 2)
                })
        segments_list.append(seg_data)

    return {
        "language": info.language,
        "duration": round(info.duration, 2),
        "segments": segments_list
    }
