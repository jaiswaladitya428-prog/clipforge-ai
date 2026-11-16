from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

class VideoMetadataResponse(BaseModel):
    id: str
    file_name: str
    file_size: int
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: str

    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    video: Optional[VideoMetadataResponse] = None

    model_config = ConfigDict(from_attributes=True)
