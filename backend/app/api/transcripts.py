import json
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.project import Project
from ..models.transcript import Transcript
from ..schemas.transcript import TranscriptResponse
from .auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Transcripts"])

def format_timestamp_srt(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

@router.get("/{project_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found"}}
        )

    transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
    if not transcript:
        return {
            "id": "",
            "project_id": project_id,
            "language": "en",
            "duration": None,
            "status": "pending",
            "error_message": None,
            "transcript_json": {"segments": []},
            "created_at": project.created_at
        }

    parsed_json = {}
    try:
        parsed_json = json.loads(transcript.transcript_json) if transcript.transcript_json else {"segments": []}
    except Exception:
        parsed_json = {"segments": []}

    return {
        "id": transcript.id,
        "project_id": transcript.project_id,
        "language": transcript.language,
        "duration": transcript.duration,
        "status": transcript.status,
        "error_message": transcript.error_message,
        "transcript_json": parsed_json,
        "created_at": transcript.created_at
    }

@router.get("/{project_id}/transcript/export")
def export_transcript(
    project_id: str,
    format: str = Query("json", pattern="^(json|srt|vtt)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project or not project.transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRANSCRIPT_NOT_FOUND", "message": "No transcript available for this project"}}
        )

    raw_data = json.loads(project.transcript.transcript_json) if project.transcript.transcript_json else {"segments": []}
    segments = raw_data.get("segments", [])

    safe_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '_', '-')).strip() or "transcript"

    if format == "json":
        formatted_json = json.dumps(raw_data, indent=2)
        return Response(
            content=formatted_json,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_transcript.json"'}
        )
    elif format == "srt":
        srt_lines = []
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp_srt(seg["start"])
            end = format_timestamp_srt(seg["end"])
            text = seg["text"]
            srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
        return Response(
            content="\n".join(srt_lines),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.srt"'}
        )
    elif format == "vtt":
        vtt_lines = ["WEBVTT\n"]
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp_vtt(seg["start"])
            end = format_timestamp_vtt(seg["end"])
            text = seg["text"]
            vtt_lines.append(f"{start} --> {end}\n{text}\n")
        return Response(
            content="\n".join(vtt_lines),
            media_type="text/vtt",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.vtt"'}
        )
