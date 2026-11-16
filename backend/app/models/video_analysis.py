from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    silence_intervals = Column(Text, nullable=True)  # JSON: [{"start": 1.0, "end": 2.5, "duration": 1.5}]
    scenes = Column(Text, nullable=True)             # JSON: [{"scene_number": 1, "start_time": 0.0, "end_time": 4.5}]
    frames = Column(Text, nullable=True)             # JSON: [{"scene_number": 1, "timestamp": 2.25, "filename": "scene_1_225ms.jpg"}]
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="analysis")
