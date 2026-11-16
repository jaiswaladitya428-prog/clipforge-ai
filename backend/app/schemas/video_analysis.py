from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class SilenceInterval(BaseModel):
    start: float
    end: float
    duration: float

class SceneItem(BaseModel):
    scene_number: int
    start_time: float
    end_time: float
    duration: float

class FrameItem(BaseModel):
    scene_number: int
    timestamp: float
    filename: str
    url: Optional[str] = None

class VideoAnalysisResponse(BaseModel):
    id: str
    project_id: str
    status: str
    silence_intervals: List[SilenceInterval] = []
    scenes: List[SceneItem] = []
    frames: List[FrameItem] = []
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
