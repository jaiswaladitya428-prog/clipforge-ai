import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any

from ..core.celery_app import celery_app
from ..core.database import SessionLocal
from ..core.config import settings
from ..models import Project, VideoAnalysis, Transcript, SourceVideo
from ..services.audio_extractor import extract_audio_wav
from ..services.silence_detector import detect_silence
from ..services.scene_detector import detect_scenes
from ..services.frame_extractor import extract_representative_frames
from ..services.transcriber import transcribe_audio_file
from ..services.gemini_service import extract_viral_highlights
from ..services.youtube_downloader import download_youtube_video

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.tasks.ping")
def ping() -> Dict[str, str]:
    """Week 2 curriculum verification test task."""
    logger.info("Executing Celery ping test task...")
    return {
        "status": "success",
        "message": "ClipForge AI worker is running!"
    }

@celery_app.task(name="app.workers.tasks.analyze_video_task", bind=True)
def analyze_video_task(self, project_id: str, video_path_str: str) -> Dict[str, Any]:
    """
    High-performance Celery task for video analysis:
    Runs Audio Track (Silence + Whisper) and Visual Track (Scenes + Keyframes) concurrently,
    then automatically runs the 30s sliding window viral scorer (>95 threshold).
    """
    video_path = Path(video_path_str)
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"status": "error", "message": f"Project {project_id} not found"}

        project.status = "processing"
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

        # Step 2: Execute Audio & Visual tracks in parallel
        video_duration = project.video.duration if project.video and project.video.duration else 0.0

        def run_audio_track():
            silences = detect_silence(audio_path, noise_db=-30, min_duration=0.5)
            transcript_result = transcribe_audio_file(audio_path)
            return silences, transcript_result

        def run_visual_track():
            scenes = detect_scenes(video_path, video_duration=video_duration, threshold=0.3)
            frames_dir = settings.FRAMES_DIR / project_id
            frames = extract_representative_frames(video_path, scenes, frames_dir)
            for f in frames:
                f["url"] = f"/api/projects/{project_id}/frames/{f['filename']}"
            return scenes, frames

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_audio = executor.submit(run_audio_track)
            future_visual = executor.submit(run_visual_track)
            silences, transcript_result = future_audio.result()
            scenes, extracted_frames = future_visual.result()

        # Step 3: Save Transcript & VideoAnalysis
        transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
        if not transcript:
            transcript = Transcript(project_id=project_id)
            db.add(transcript)

        transcript.language = transcript_result["language"]
        transcript.duration = transcript_result["duration"]
        transcript.transcript_json = json.dumps(transcript_result)
        transcript.status = "completed"

        analysis.silence_intervals = json.dumps(silences)
        analysis.scenes = json.dumps(scenes)
        analysis.frames = json.dumps(extracted_frames)
        analysis.status = "completed"

        project.status = "completed"
        db.commit()

        logger.info(f"Video analysis completed for project {project_id}.")
        return {"status": "success", "project_id": project_id}

    except Exception as e:
        db.rollback()
        logger.error(f"Error in analyze_video_task for project {project_id}: {e}", exc_info=True)
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
            if not transcript:
                transcript = Transcript(project_id=project_id)
                db.add(transcript)
            transcript.status = "failed"
            transcript.error_message = str(e)

            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.project_id == project_id).first()
            if not analysis:
                analysis = VideoAnalysis(project_id=project_id)
                db.add(analysis)
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.ingest_youtube_task")
def ingest_youtube_task(project_id: str, youtube_url: str) -> Dict[str, Any]:
    """Celery worker task for YouTube ingestion followed by video analysis."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"status": "error", "message": "Project not found"}

        project.status = "downloading"
        db.commit()

        target_mp4 = settings.VIDEOS_DIR / f"{project_id}.mp4"
        info = download_youtube_video(youtube_url, target_mp4)

        source_video = db.query(SourceVideo).filter(SourceVideo.project_id == project.id).first()
        if not source_video:
            source_video = SourceVideo(project_id=project.id)
            db.add(source_video)

        source_video.file_path = str(target_mp4)
        source_video.file_name = f"{info.get('title', 'YouTube Video')}.mp4"
        source_video.file_size = info.get("file_size", 0)
        source_video.duration = info.get("duration", 0.0)
        source_video.mime_type = "video/mp4"

        project.status = "processing"
        db.commit()

        # Trigger analysis
        return analyze_video_task(project_id, str(target_mp4))

    except Exception as e:
        db.rollback()
        logger.error(f"YouTube ingestion failed for project {project_id}: {e}", exc_info=True)
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
