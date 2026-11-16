# Tasks: ClipForge AI (Phase 1 Foundation)

---

## Phase 1: Foundation & Project Setup

### Task 1: Initialize Monorepo Structure & FastAPI Backend Skeleton
- [x] Monorepo layout created with `backend/` and `frontend/` folders.
- [x] Python virtual environment created with `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pydantic-settings`, and `python-multipart`.
- [x] Database engine and base session factory configured for SQLite (`clipforge.db`).
- [x] `GET /api/health` returns `{"status": "ok"}`.

### Task 2: Initialize Next.js 14+ Frontend Shell with Tailwind CSS
- [x] Next.js app created with App Router, TypeScript, and Tailwind CSS.
- [x] Base layout includes a header with logo/branding ("ClipForge AI") and theme styling.
- [x] Centralized API utility (`lib/api.ts`) configured to communicate with `http://localhost:8000/api`.

## Checkpoint 1: Foundation
- [x] FastAPI backend starts, database initializes, health check returns `{"status": "ok"}`.
- [x] Next.js frontend builds without error and renders home view.
- [x] Human review of project structure before proceeding to Auth.

---

## Phase 2: User Authentication (Vertical Slice 1)

### Task 3: Backend Authentication Engine (User Model, Password Hashing, JWT Endpoints)
- [x] `User` model created with `id`, `name`, `email` (unique), `password_hash`, and `created_at`.
- [x] Password hashing via clean `bcrypt` and JWT token issuance using `PyJWT`.
- [x] `POST /api/auth/register` creates user and returns token.
- [x] `POST /api/auth/login` validates credentials and returns token.
- [x] `GET /api/auth/me` returns current user profile when given valid Bearer token, or 401 when unauthenticated.

### Task 4: Frontend Authentication Flows (Sign Up, Login, Session Context)
- [x] `/register` page with form fields for Name, Email, Password, and error message handling.
- [x] `/login` page with Email, Password, and session persistence.
- [x] `AuthContext` providing `user`, `login()`, `logout()`, and `isAuthenticated` states.
- [x] Navigation header updates to show user name & Logout button when authenticated.

## Checkpoint 2: Authentication
- [x] End-to-end user registration works from UI to database.
- [x] User can log in, stay logged in across page reloads, and log out.
- [x] Protected endpoints securely block invalid tokens with 401 Unauthorized.

---

## Phase 3: Project Management & Video Ingestion (Vertical Slice 2)

### Task 5: Projects Dashboard & Database Models
- [x] `Project` model created with `id`, `user_id`, `title`, `description`, `status` (`created`, `processing`, `completed`), and `created_at`.
- [x] Endpoints `POST /api/projects` and `GET /api/projects` filtered by authenticated user.
- [x] `/dashboard` page listing all projects for the logged-in user with status badges.
- [x] "New Project" dialog/modal to create a project with a custom title.

### Task 6: Video Upload Pipeline, Local Storage & Metadata Extraction
- [x] `SourceVideo` model created with `id`, `project_id`, `file_path`, `file_name`, `file_size`, `duration`, `width`, `height`, `mime_type`.
- [x] `POST /api/projects/{id}/upload` accepts multipart video files (MP4, MOV, WebM).
- [x] Validates file type and size (limit configured, e.g. 500MB).
- [x] Extracts duration, dimensions, and codec info and writes record to `source_videos`.
- [x] Drag-and-drop upload component in frontend with upload progress bar.

## Checkpoint 3: Video Ingestion
- [x] User can create a project, drag-and-drop an MP4 video, and see upload progress.
- [x] Backend stores video file and extracts duration, resolution, and codec metadata.
- [x] Project page displays uploaded video preview and extracted specs.

---

## Phase 4: Audio Extraction & faster-whisper Transcription (Vertical Slice 3)

### Task 7: Audio Extraction Pipeline (FFmpeg / imageio-ffmpeg)
- [x] `AudioExtractor` service extracts 16kHz mono 16-bit PCM WAV audio from any supported video container.
- [x] Uses bundled/python `imageio-ffmpeg` binary with graceful fallback to system `ffmpeg`.
- [x] Handles corrupted or audio-less videos with descriptive error states.
- [x] Triggered automatically upon upload in background processing pipeline.

### Task 8: faster-whisper Transcription Engine & Timestamped JSON Output
- [x] `faster-whisper` dependency installed and configured (`model_size_or_path="base"`, `device="cpu"`, `compute_type="int8"`).
- [x] `Transcript` model created with `id`, `project_id`, `language`, `duration`, `transcript_json`, `created_at`.
- [x] Background job executes transcription, parses segments with start/end timestamps, and saves JSON.
- [x] `GET /api/projects/{id}/transcript` returns structured timestamped JSON.

### Task 9: Interactive Synced Transcript Player & JSON Export UI
- [x] Video player synchronized with transcript: current transcript segment highlights as video plays.
- [x] Clicking any transcript line seeks the video to that exact `start` timestamp.
- [x] "Download JSON" button exports the full timestamped transcript as a `.json` file.
- [x] "Download SRT" and "Download VTT" subtitle exports also supported.
- [x] "Copy JSON" button copies formatted JSON to clipboard.
- [x] Status banner displays current pipeline stage: Uploaded -> Extracting Audio -> Transcribing -> Ready.

## Checkpoint 4: Complete Phase 1 MVP
- [x] User can sign up, log in, create a project, and upload a raw video.
- [x] Audio is extracted and `faster-whisper` generates timestamped transcript segments in JSON.
- [x] User can play the video synchronized with the transcript, seek by clicking text, and export the timestamped JSON file.
- [x] All unit and API integration tests pass clean.
