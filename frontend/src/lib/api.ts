const API_BASE = "http://localhost:8000/api";

export interface ApiError {
  code: string;
  message: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface VideoMetadata {
  id: string;
  file_name: string;
  file_size: number;
  duration?: number;
  width?: number;
  height?: number;
  mime_type: string;
}

export interface Project {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: "created" | "uploading" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  video?: VideoMetadata;
}

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  probability: number;
}

export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  words?: WordTimestamp[];
}

export interface TranscriptData {
  language: string;
  duration: number;
  segments: TranscriptSegment[];
}

export interface TranscriptResponse {
  id: string;
  project_id: string;
  language: string;
  duration?: number;
  status: "pending" | "processing" | "completed" | "failed";
  error_message?: string;
  transcript_json: TranscriptData;
  created_at: string;
}

export interface SilenceInterval {
  start: number;
  end: number;
  duration: number;
}

export interface SceneItem {
  scene_number: number;
  start_time: number;
  end_time: number;
  duration: number;
}

export interface FrameItem {
  scene_number: number;
  timestamp: number;
  filename: string;
  url?: string;
}

export interface VideoAnalysisResponse {
  id: string;
  project_id: string;
  status: string;
  silence_intervals: SilenceInterval[];
  scenes: SceneItem[];
  frames: FrameItem[];
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface ViralHighlight {
  start_time: number;
  end_time: number;
  hook_title: string;
  viral_score: number;
  reasoning: string;
  suggested_theme: string;
  suggested_caption_style: string;
}

export interface ViralHighlightResponse {
  highlights: ViralHighlight[];
}

export interface RenderCaptionItem {
  start: number;
  end: number;
  text: string;
  words?: WordTimestamp[];
}

export interface RenderRequest {
  start_time: number;
  end_time: number;
  aspect_ratio: "9:16" | "16:9";
  theme: "minimal" | "blueprint" | "anime" | "ghibli" | "papercut";
  caption_style: "karaoke" | "sentence";
  captions: RenderCaptionItem[];
}

export interface RenderJobResponse {
  render_id: string;
  status: "queued" | "rendering" | "completed" | "failed";
  progress: number;
  download_url?: string;
  error?: string;
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("clipforge_token") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null as unknown as T;
  }

  const data = await response.json();

  if (!response.ok) {
    const errorMsg = data?.detail?.error?.message || data?.detail || "An unexpected error occurred.";
    const errorCode = data?.detail?.error?.code || "API_ERROR";
    const err = new Error(errorMsg) as Error & { code?: string };
    err.code = errorCode;
    throw err;
  }

  return data as T;
}
