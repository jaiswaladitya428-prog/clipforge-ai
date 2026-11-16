import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db, SessionLocal
from ..models.user import User
from ..models.project import Project
from ..models.source_video import SourceVideo
from ..models.transcript import Transcript
from ..models.video_analysis import VideoAnalysis
from ..schemas.project import ProjectResponse
from ..schemas.video_analysis import VideoAnalysisResponse
from ..schemas.render import (
    ViralHighlightResponse,
    ViralHighlightItem,
    RenderRequest,
    RenderJobResponse
)
from ..services.ffmpeg_utils import extract_video_metadata
from ..services.audio_extractor import extract_audio_wav
from ..services.silence_detector import detect_silence
from ..services.scene_detector import detect_scenes
from ..services.frame_extractor import extract_representative_frames
from ..services.transcriber import transcribe_audio_file
from ..services.gemini_service import extract_viral_highlights
from ..services.subtitle_generator import generate_ass_subtitle_file
from ..services.video_renderer import render_styled_video
from .auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Videos & Processing"])

ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",  # .mov
    "video/webm",
    "video/x-matroska", # .mkv
}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB limit

def process_video_pipeline(project_id: str, video_path: Path):
    """Background worker pipeline: Audio extraction, silence detection, scene detection, keyframes, and Whisper transcription."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        project.status = "processing"
        
        # Ensure VideoAnalysis record exists
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.project_id == project_id).first()
        if not analysis:
            analysis = VideoAnalysis(project_id=project_id)
            db.add(analysis)
        analysis.status = "processing"
        analysis.error_message = None
        db.commit()

        # Step 1: Extract 16kHz mono WAV audio
        audio_filename = f"{project_id}_audio.wav"
        audio_path = settings.AUDIO_DIR / audio_filename
        extract_audio_wav(video_path, audio_path)

        # Step 2: Detect Silence Intervals
        silences = detect_silence(audio_path, noise_db=-30, min_duration=0.5)

        # Step 3: Detect Visual Scene Changes
        video_duration = project.video.duration if project.video and project.video.duration else 0.0
        scenes = detect_scenes(video_path, video_duration=video_duration, threshold=0.3)

        # Step 4: Extract Representative Keyframes for each scene
        frames_dir = settings.FRAMES_DIR / project_id
        extracted_frames = extract_representative_frames(video_path, scenes, frames_dir)

        # Add public URL reference for each frame
        for f in extracted_frames:
            f["url"] = f"/api/projects/{project_id}/frames/{f['filename']}"

        # Step 5: Transcribe via faster-whisper (CPU int8)
        transcript_result = transcribe_audio_file(audio_path)

        # Step 6: Save Transcript
        transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
        if not transcript:
            transcript = Transcript(project_id=project_id)
            db.add(transcript)

        transcript.language = transcript_result["language"]
        transcript.duration = transcript_result["duration"]
        transcript.transcript_json = json.dumps(transcript_result)
        transcript.status = "completed"

        # Step 7: Save VideoAnalysis
        analysis.silence_intervals = json.dumps(silences)
        analysis.scenes = json.dumps(scenes)
        analysis.frames = json.dumps(extracted_frames)
        analysis.status = "completed"

        project.status = "completed"
        db.commit()
    except Exception as e:
        db.rollback()
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
            if not transcript:
                transcript = Transcript(project_id=project_id)
                db.add(transcript)
            transcript.status = "failed"
            transcript.error_message = str(e)
            transcript.transcript_json = json.dumps({"segments": []})

            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.project_id == project_id).first()
            if not analysis:
                analysis = VideoAnalysis(project_id=project_id)
                db.add(analysis)
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.post("/{project_id}/upload", response_model=ProjectResponse)
async def upload_video(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
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

    content_type = file.content_type or "video/mp4"
    if content_type not in ALLOWED_MIME_TYPES and not file.filename.lower().endswith(('.mp4', '.mov', '.webm', '.mkv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_FILE_TYPE", "message": "Only MP4, MOV, WebM, and MKV video files are supported."}}
        )

    file_ext = Path(file.filename).suffix or ".mp4"
    saved_filename = f"{project_id}{file_ext}"
    saved_path = settings.VIDEOS_DIR / saved_filename

    total_bytes = 0
    with open(saved_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE:
                saved_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={"error": {"code": "FILE_TOO_LARGE", "message": "File exceeds 500 MB limit."}}
                )
            buffer.write(chunk)

    duration, width, height = extract_video_metadata(saved_path)

    source_video = db.query(SourceVideo).filter(SourceVideo.project_id == project.id).first()
    if not source_video:
        source_video = SourceVideo(project_id=project.id)
        db.add(source_video)

    source_video.file_path = str(saved_path)
    source_video.file_name = file.filename
    source_video.file_size = total_bytes
    source_video.duration = duration
    source_video.width = width
    source_video.height = height
    source_video.mime_type = content_type

    project.status = "processing"
    db.commit()
    db.refresh(project)

    background_tasks.add_task(process_video_pipeline, project.id, saved_path)
    return project

@router.post("/{project_id}/retry", response_model=ProjectResponse)
def retry_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry analysis pipeline on an existing uploaded video."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project or not project.video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "VIDEO_NOT_FOUND", "message": "No video found to retry analysis."}}
        )

    video_path = Path(project.video.file_path)
    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FILE_MISSING", "message": "Source video file is missing from disk."}}
        )

    project.status = "processing"
    db.commit()
    db.refresh(project)

    background_tasks.add_task(process_video_pipeline, project.id, video_path)
    return project

@router.get("/{project_id}/analysis", response_model=VideoAnalysisResponse)
def get_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full video analysis report including scenes, silence intervals, and frames."""
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

    analysis = db.query(VideoAnalysis).filter(VideoAnalysis.project_id == project_id).first()
    if not analysis:
        return {
            "id": "",
            "project_id": project_id,
            "status": "pending",
            "silence_intervals": [],
            "scenes": [],
            "frames": [],
            "error_message": None,
            "created_at": project.created_at,
            "updated_at": project.created_at
        }

    return {
        "id": analysis.id,
        "project_id": analysis.project_id,
        "status": analysis.status,
        "silence_intervals": json.loads(analysis.silence_intervals) if analysis.silence_intervals else [],
        "scenes": json.loads(analysis.scenes) if analysis.scenes else [],
        "frames": json.loads(analysis.frames) if analysis.frames else [],
        "error_message": analysis.error_message,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at
    }

@router.get("/{project_id}/frames/{filename}")
def get_frame(
    project_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream a representative keyframe image."""
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

    # Sanitize filename
    safe_filename = Path(filename).name
    frame_path = settings.FRAMES_DIR / project_id / safe_filename
    if not frame_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FRAME_NOT_FOUND", "message": "Frame image not found."}}
        )

    return FileResponse(path=str(frame_path), media_type="image/jpeg", filename=safe_filename)

@router.get("/{project_id}/video/stream")
def stream_video(
    project_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )
    if not project or not project.video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "VIDEO_NOT_FOUND", "message": "No video associated with this project"}}
        )

    video_path = Path(project.video.file_path)
    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FILE_MISSING", "message": "Video file not found on disk"}}
        )

    return FileResponse(
        path=str(video_path),
        media_type=project.video.mime_type,
        filename=project.video.file_name
    )

# -------------------------------------------------------------
# Studio Highlights & Render Engine
# -------------------------------------------------------------
render_jobs: Dict[str, Dict[str, Any]] = {}

def execute_render_job(
    render_id: str,
    project_id: str,
    video_path: Path,
    req: RenderRequest,
    sub_path: Optional[Path],
    output_path: Path
):
    try:
        render_jobs[render_id]["status"] = "rendering"
        render_jobs[render_id]["progress"] = 25

        target_w = 1080 if req.aspect_ratio == "9:16" else 1920
        target_h = 1920 if req.aspect_ratio == "9:16" else 1080

        # Generate ASS subtitles if captions are provided
        if req.captions and sub_path:
            caption_dicts = [c.model_dump() for c in req.captions]
            generate_ass_subtitle_file(
                segments=caption_dicts,
                output_path=sub_path,
                clip_start=req.start_time,
                clip_end=req.end_time,
                theme=req.theme,
                caption_style=req.caption_style,
                target_width=target_w,
                target_height=target_h
            )

        render_jobs[render_id]["progress"] = 50

        render_styled_video(
            input_video_path=video_path,
            output_video_path=output_path,
            start_time=req.start_time,
            end_time=req.end_time,
            aspect_ratio=req.aspect_ratio,
            theme=req.theme,
            subtitle_ass_path=sub_path if (req.captions and sub_path and sub_path.exists()) else None
        )

        render_jobs[render_id]["status"] = "completed"
        render_jobs[render_id]["progress"] = 100
        render_jobs[render_id]["download_url"] = f"/api/projects/{project_id}/render/{render_id}/download"
    except Exception as e:
        render_jobs[render_id]["status"] = "failed"
        render_jobs[render_id]["error"] = str(e)

@router.post("/{project_id}/ai-highlight", response_model=ViralHighlightResponse)
def get_ai_viral_highlights(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze video transcript via Gemini to recommend viral 30-60s clip(s)."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project or not project.transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRANSCRIPT_NOT_FOUND", "message": "No transcript available for this project yet."}}
        )

    transcript_data = {}
    if project.transcript.transcript_json:
        try:
            transcript_data = json.loads(project.transcript.transcript_json)
        except Exception:
            transcript_data = {}

    segments = transcript_data.get("segments", [])
    duration = project.video.duration if project.video and project.video.duration else 0.0

    raw_clips = extract_viral_highlights(segments, video_duration=duration)
    highlights = [ViralHighlightItem(**c) for c in raw_clips]
    return ViralHighlightResponse(highlights=highlights)

@router.post("/{project_id}/render", response_model=RenderJobResponse)
def start_render_job(
    project_id: str,
    request: RenderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger background FFmpeg render for a trimmed, themed clip."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project or not project.video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "VIDEO_NOT_FOUND", "message": "No video found for this project"}}
        )

    video_path = Path(project.video.file_path)
    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FILE_MISSING", "message": "Original video file is missing on disk"}}
        )

    if request.start_time >= request.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_TIMESTAMPS", "message": "start_time must be less than end_time"}}
        )

    render_id = str(uuid.uuid4())
    output_filename = f"{project_id}_{render_id}.mp4"
    output_path = settings.RENDERS_DIR / output_filename
    sub_path = settings.RENDERS_DIR / f"{project_id}_{render_id}.ass"

    render_jobs[render_id] = {
        "render_id": render_id,
        "project_id": project_id,
        "status": "queued",
        "progress": 5,
        "output_path": str(output_path),
        "download_url": None,
        "error": None
    }

    background_tasks.add_task(
        execute_render_job,
        render_id,
        project_id,
        video_path,
        request,
        sub_path if request.captions else None,
        output_path
    )

    return RenderJobResponse(
        render_id=render_id,
        status="queued",
        progress=5
    )

@router.get("/{project_id}/render/{render_id}/status", response_model=RenderJobResponse)
def get_render_job_status(
    project_id: str,
    render_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check status of a background render job."""
    if render_id not in render_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RENDER_NOT_FOUND", "message": "Render job not found"}}
        )

    job = render_jobs[render_id]
    return RenderJobResponse(
        render_id=job["render_id"],
        status=job["status"],
        progress=job["progress"],
        download_url=job.get("download_url"),
        error=job.get("error")
    )

@router.get("/{project_id}/render/{render_id}/download")
def download_rendered_video(
    project_id: str,
    render_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Download or stream the rendered MP4 video file."""
    if render_id not in render_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RENDER_NOT_FOUND", "message": "Render job not found"}}
        )

    job = render_jobs[render_id]
    output_path = Path(job.get("output_path", ""))
    if not output_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "OUTPUT_MISSING", "message": "Rendered video file is missing or still processing"}}
        )

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=f"clipforge_{project_id[:8]}_{render_id[:8]}.mp4"
    )

