from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict

class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    probability: float

class SegmentTimestamp(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: Optional[List[WordTimestamp]] = None

class TranscriptData(BaseModel):
    language: str
    duration: float
    segments: List[SegmentTimestamp]

class TranscriptResponse(BaseModel):
    id: str
    project_id: str
    language: str
    duration: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    transcript_json: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
