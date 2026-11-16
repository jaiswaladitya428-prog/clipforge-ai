# Implementation Plan: ClipForge AI (Phase 1 Foundation)

## Overview
ClipForge AI is an automated video editing web application. This implementation plan covers the core Phase 1 foundation: a modern Next.js frontend and Python FastAPI backend running locally on Windows 11. It implements secure user authentication, project creation, drag-and-drop video ingestion with metadata extraction, and speech-to-text transcription powered by `faster-whisper` (running on CPU with INT8 quantization) to generate timestamped JSON transcripts alongside a synced video preview.

## Architecture Decisions
- **Repository Structure:** Monorepo with `frontend/` (Next.js 14 App Router, TypeScript, Tailwind CSS) and `backend/` (FastAPI, Python 3.12).
- **Database & ORM:** SQLite via SQLAlchemy for fast, zero-friction local development without requiring external database server daemons initially, with architecture cleanly portable to PostgreSQL.
- **Authentication:** JWT (JSON Web Tokens) with password hashing via `passlib[bcrypt]` and `python-jose`/`PyJWT`, stored in secure HTTP-only cookies / local storage.
- **Media Processing & Storage:** Local filesystem storage (`backend/storage/videos/` and `backend/storage/audio/`). FFmpeg binary handled via system PATH or `imageio-ffmpeg` to guarantee reliable audio extraction on Windows without missing-dependency errors.
- **Speech Recognition:** `faster-whisper` utilizing `base` or `small` model configured for `device="cpu"` and `compute_type="int8"` to remain well within the 8 GB RAM constraint of the Windows machine while delivering fast, accurate timestamps.
- **Asynchronous Execution:** FastAPI `BackgroundTasks` for local execution of audio extraction and transcription jobs, updating job statuses in the database for client polling/progress.

---

## Task List

### Phase 1: Foundation & Project Setup
- [ ] **Task 1:** Initialize Monorepo Structure & FastAPI Backend Skeleton
- [ ] **Task 2:** Initialize Next.js 14+ Frontend Shell with Tailwind CSS

### Checkpoint: Foundation
- [ ] FastAPI backend starts, database initializes, health-check endpoint responds `200 OK`.
- [ ] Next.js frontend runs and renders base application layout.

### Phase 2: User Authentication (Vertical Slice 1)
- [ ] **Task 3:** Backend Authentication Engine (User Model, Password Hashing, JWT Endpoints)
- [ ] **Task 4:** Frontend Authentication Flows (Sign Up, Login, Session Context)

### Checkpoint: Authentication
- [ ] User can register a new account, log in, receive a valid JWT token, and access protected routes.
- [ ] Unauthenticated requests are rejected with 401 Unauthorized.

### Phase 3: Project Management & Video Ingestion (Vertical Slice 2)
- [ ] **Task 5:** Projects Dashboard & Database Models
- [ ] **Task 6:** Video Upload Pipeline, Local Storage & Metadata Extraction

### Checkpoint: Video Ingestion
- [ ] Logged-in user can create a project and upload an MP4/MOV/WebM video.
- [ ] File is safely stored locally, metadata (duration, resolution, format) is extracted and saved to DB.

### Phase 4: Audio Extraction & faster-whisper Transcription (Vertical Slice 3)
- [ ] **Task 7:** Audio Extraction Pipeline (FFmpeg / imageio-ffmpeg)
- [ ] **Task 8:** faster-whisper Transcription Engine & Timestamped JSON Output
- [ ] **Task 9:** Interactive Synced Transcript Player & JSON Export UI

### Checkpoint: Complete Phase 1 MVP
- [ ] User uploads video -> backend extracts audio -> `faster-whisper` transcribes speech.
- [ ] Project workspace displays video player synchronized with clickable timestamped transcript.
- [ ] User can inspect and download the raw timestamped JSON transcript.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing system FFmpeg on Windows | High | Bundle or integrate `imageio-ffmpeg` as fallback so audio extraction works immediately without manual PATH configuration. |
| 8 GB RAM memory pressure during Whisper inference | High | Default to `faster-whisper` `base` model with `compute_type="int8"` on CPU (~300MB VRAM/RAM footprint). |
| Video upload timeout or failure on large files | Medium | Implement streaming file uploads with chunked writes and enforce sensible initial file limits (e.g., 200MB–500MB). |
| Long blocking requests during transcription | High | Run transcription in FastAPI `BackgroundTasks` and update task status (`pending`, `processing`, `completed`, `failed`) for client polling. |

---

## Open Questions
- What default model size would you like for initial testing (`tiny`, `base`, or `small`)? *Defaulting to `base` (int8) for ideal speed/accuracy balance on 8 GB RAM.*
- Preferred subtitle format alongside JSON: Include `.srt` and `.vtt` export options in addition to raw JSON?

