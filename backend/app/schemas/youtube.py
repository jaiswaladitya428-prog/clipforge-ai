from pydantic import BaseModel, Field

class YouTubeImportRequest(BaseModel):
    url: str = Field(..., description="YouTube video or live stream URL")
