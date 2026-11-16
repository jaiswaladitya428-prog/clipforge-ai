from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .core.config import settings
from .core.database import engine, Base
from .api import auth, projects, videos, transcripts

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for ClipForge AI: Video processing and timestamped transcription engine.",
    version="1.0.0"
)

# CORS configuration to allow local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route: redirect directly to interactive API documentation
@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

# Mount API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(transcripts.router, prefix="/api")

@app.get("/api", tags=["Root"])
def api_root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "whisper_model": settings.WHISPER_MODEL,
        "compute_type": settings.WHISPER_COMPUTE_TYPE,
        "device": settings.WHISPER_DEVICE
    }
