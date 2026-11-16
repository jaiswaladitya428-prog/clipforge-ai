from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    language = Column(String(10), default="en")
    duration = Column(Float, nullable=True)
    transcript_json = Column(Text, nullable=False)  # JSON string containing segments and words
    status = Column(String(50), default="pending")  # pending, transcribing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="transcript")
