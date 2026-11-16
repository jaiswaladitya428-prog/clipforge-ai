from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ViralHighlightItem(BaseModel):
    start_time: float
    end_time: float
    hook_title: str
    viral_score: int
    reasoning: str
    suggested_theme: str = "minimal"
    suggested_caption_style: str = "karaoke"

class ViralHighlightResponse(BaseModel):
    highlights: List[ViralHighlightItem]

class CaptionItem(BaseModel):
    start: float
    end: float
    text: str
    words: Optional[List[Dict[str, Any]]] = None

class RenderRequest(BaseModel):
    start_time: float
    end_time: float
    aspect_ratio: str = Field("9:16", pattern="^(9:16|16:9)$")
    theme: str = Field("minimal", pattern="^(minimal|blueprint|anime|ghibli|papercut)$")
    caption_style: str = Field("karaoke", pattern="^(karaoke|sentence)$")
    captions: Optional[List[CaptionItem]] = None

class RenderJobResponse(BaseModel):
    render_id: str
    status: str  # "rendering", "completed", "failed"
    progress: int = 0
    download_url: Optional[str] = None
    error: Optional[str] = None
