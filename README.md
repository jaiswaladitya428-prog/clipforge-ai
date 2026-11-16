# ClipForge AI

ClipForge AI is an intelligent, automated video analysis and transcription platform designed to process raw video footage into word-level timestamped transcripts, detected scene boundaries, keyframe thumbnails, and silence intervals.

---

## Architecture & Analysis Pipeline

```
                     ┌───────────────────────────┐
                     │ Raw Video (MP4/MOV/WebM)  │
                     └─────────────┬─────────────┘
                                   │
                         [ Video Ingestion ]
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
    [ Audio Extraction ]                      [ Scene & Keyframe ]
  16kHz Mono 16-bit WAV                      Visual cut detection
  (imageio-ffmpeg engine)                   & keyframe thumbnails
              │                                         │
        ┌─────┴──────────────┐                          │
        ▼                    ▼                          │
[ Silence Detection ]  [ faster-whisper ]               │
  FFmpeg -af            CPU (INT8) speech-to-text        │
  silencedetect         Word & segment timestamps       │
        │                    │                          │
        └──────────────┬─────┴──────────────────────────┘
                       ▼
            [ Analysis Report ]
       Saved to Database (PostgreSQL / SQLite)
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[ Next.js Workspace ]         [ Multi-Format Exports ]
Synced player & timeline       JSON / SRT / VTT Subtitles
```

### 1. Ingestion & Audio Extraction
- Accepts MP4, MOV, WebM, and MKV video formats.
- Extracts video metadata (duration, width, height, codec).
- Extracts a standardized 16kHz 16-bit mono WAV file using embedded `imageio-ffmpeg` to prevent Windows PATH dependency failures.

### 2. Speech Transcription (faster-whisper)
- Runs OpenAI's Whisper model converted to CTranslate2 via `faster-whisper`.
- Optimized for Windows 11 and 8 GB RAM by running on CPU with INT8 quantization (`compute_type="int8"`).
- Produces word-level and sentence-level timestamps with millisecond accuracy.

### 3. Silence & Pause Detection
- Uses FFmpeg's `silencedetect` audio filter (`noise=-30dB:d=0.5s`).
- Identifies dead space and long pauses for automated jump-cuts and pacing adjustments.

### 4. Scene Boundary & Keyframe Extraction
- Analyzes video frames to detect scene transitions.
- Extracts representative keyframe images (`.jpg`) for every scene and saves them in `backend/storage/frames/{project_id}/`.

### 5. Multi-Format Exports
- **JSON:** Complete structured transcript including word-level timestamps, confidence scores, and segment offsets.
- **SubRip (.srt):** Standard subtitle file with `00:00:00,000` timestamps.
- **WebVTT (.vtt):** Modern web video text tracks format.

---

## Database Configuration (PostgreSQL & SQLite)

The platform uses SQLAlchemy ORM with support for both SQLite and PostgreSQL.

### Default (SQLite)
By default, the backend creates `backend/clipforge.db` automatically with zero setup:
```
DATABASE_URL="sqlite:///clipforge.db"
```

### PostgreSQL Setup
To connect to a managed or local PostgreSQL database, set the environment variable:
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://username:password@localhost:5432/clipforge_db"
```
Or create a `backend/.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/clipforge_db
SECRET_KEY=your-secure-secret-key
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create account (returns JWT token)
- `POST /api/auth/login` - Authenticate user
- `GET /api/auth/me` - Get current user profile

### Projects & Analysis
- `GET /api/projects` - List all projects for authenticated user
- `POST /api/projects` - Create a new video project
- `GET /api/projects/{id}` - Get project status and metadata
- `DELETE /api/projects/{id}` - Delete project and stored files
- `POST /api/projects/{id}/upload` - Upload video file and start pipeline
- `POST /api/projects/{id}/retry` - Re-trigger analysis on failed video
- `GET /api/projects/{id}/analysis` - Retrieve full report (silence, scenes, frames)
- `GET /api/projects/{id}/transcript` - Retrieve timestamped speech transcript
- `GET /api/projects/{id}/transcript/export?format=json|srt|vtt` - Download subtitles
- `GET /api/projects/{id}/frames/{filename}` - Stream extracted keyframe image
- `GET /api/projects/{id}/video/stream` - Stream video to HTML5 player

---

## Getting Started

### 1. Prerequisites
- Python 3.11 or 3.12 (`py` launcher or `uv`)
- Node.js 18+ and npm

### 2. Backend Setup
```powershell
cd backend
# Create virtual environment & install dependencies
uv venv .venv --python 3.11
uv pip install -r requirements.txt --python .venv\Scripts\python.exe

# Start development server
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
Interactive API documentation: `http://localhost:8000/docs`

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open web application: `http://localhost:3000`

### 4. Running Automated Tests
```powershell
cd backend
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
