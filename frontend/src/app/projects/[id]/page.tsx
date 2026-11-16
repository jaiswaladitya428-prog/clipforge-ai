"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  apiFetch,
  Project,
  TranscriptResponse,
  VideoAnalysisResponse,
  ViralHighlight,
  ViralHighlightResponse,
  RenderCaptionItem,
  RenderRequest,
  RenderJobResponse,
} from "@/lib/api";
import { VideoUploader } from "@/components/VideoUploader";
import { StudioPlayer } from "@/components/StudioPlayer";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { CaptionEditor } from "@/components/CaptionEditor";
import { RenderModal } from "@/components/RenderModal";
import { JsonExportModal } from "@/components/JsonExportModal";
import {
  ArrowLeft,
  Loader2,
  FileJson,
  AlertCircle,
  RefreshCw,
  Film,
  Sparkles,
  Layers,
  VolumeX,
  FileText,
  RotateCcw,
  Flame,
  Scissors,
  Smartphone,
  Monitor,
  Palette,
  Type,
  Sliders,
  Check,
} from "lucide-react";

export default function ProjectWorkspacePage() {
  const { id } = useParams() as { id: string };
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [project, setProject] = useState<Project | null>(null);
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);
  const [analysis, setAnalysis] = useState<VideoAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [seekTime, setSeekTime] = useState<number | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Studio Edit Controls State
  const [activeTab, setActiveTab] = useState<"subtitles" | "transcript" | "scenes">("subtitles");
  const [trimStart, setTrimStart] = useState<number>(0);
  const [trimEnd, setTrimEnd] = useState<number>(30);
  const [aspectRatio, setAspectRatio] = useState<"9:16" | "16:9">("9:16");
  const [theme, setTheme] = useState<"minimal" | "blueprint" | "anime" | "ghibli" | "papercut">("anime");
  const [captionStyle, setCaptionStyle] = useState<"karaoke" | "sentence">("karaoke");
  const [captions, setCaptions] = useState<RenderCaptionItem[]>([]);

  // AI Highlights State
  const [highlights, setHighlights] = useState<ViralHighlight[]>([]);
  const [loadingHighlights, setLoadingHighlights] = useState(false);
  const [highlightError, setHighlightError] = useState<string | null>(null);

  // Render & Export State
  const [renderJob, setRenderJob] = useState<RenderJobResponse | null>(null);
  const [rendering, setRendering] = useState(false);
  const [showRenderModal, setShowRenderModal] = useState(false);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const renderPollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchProjectData = useCallback(async () => {
    try {
      const proj = await apiFetch<Project>(`/projects/${id}`);
      setProject(proj);

      if (proj.status === "completed" || proj.status === "processing") {
        const [trans, anal] = await Promise.all([
          apiFetch<TranscriptResponse>(`/projects/${id}/transcript`).catch(() => null),
          apiFetch<VideoAnalysisResponse>(`/projects/${id}/analysis`).catch(() => null),
        ]);
        if (trans) {
          setTranscript(trans);
          // Initialize captions and trim
          if (trans.transcript_json?.segments) {
            setCaptions(
              trans.transcript_json.segments.map((s) => ({
                start: s.start,
                end: s.end,
                text: s.text,
                words: s.words || [],
              }))
            );
          }
        }
        if (anal) setAnalysis(anal);
      }

      // Initialize default trim range once project duration is known
      if (proj.video?.duration && proj.video.duration > 0) {
        setTrimEnd((prev) => (prev === 30 ? Math.min(35, proj.video!.duration!) : prev));
      }

      return proj;
    } catch (err: any) {
      setError(err.message || "Failed to load project");
      return null;
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    } else if (user && id) {
      fetchProjectData().then((proj) => {
        if (proj && proj.status === "processing") {
          startPolling();
        }
      });
    }

    return () => {
      stopPolling();
      stopRenderPolling();
    };
  }, [user, authLoading, id, router, fetchProjectData]);

  const startPolling = () => {
    stopPolling();
    pollIntervalRef.current = setInterval(async () => {
      const proj = await fetchProjectData();
      if (proj && proj.status !== "processing") {
        stopPolling();
      }
    }, 2500);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const stopRenderPolling = () => {
    if (renderPollRef.current) {
      clearInterval(renderPollRef.current);
      renderPollRef.current = null;
    }
  };

  const handleUploadDone = () => {
    fetchProjectData();
    startPolling();
  };

  const handleRetry = async () => {
    setRetrying(true);
    setError(null);
    try {
      await apiFetch(`/projects/${id}/retry`, { method: "POST" });
      fetchProjectData();
      startPolling();
    } catch (err: any) {
      setError(err.message || "Failed to retry analysis job.");
    } finally {
      setRetrying(false);
    }
  };

  // Fetch AI Viral Highlights via Gemini
  const handleFindViralClips = async () => {
    setLoadingHighlights(true);
    setHighlightError(null);
    try {
      const res = await apiFetch<ViralHighlightResponse>(`/projects/${id}/ai-highlight`, {
        method: "POST",
      });
      setHighlights(res.highlights || []);
      // If highlights found, auto-apply the top recommended clip
      if (res.highlights && res.highlights.length > 0) {
        applyHighlight(res.highlights[0]);
      }
    } catch (err: any) {
      setHighlightError(err.message || "Failed to retrieve AI viral recommendations.");
    } finally {
      setLoadingHighlights(false);
    }
  };

  const applyHighlight = (h: ViralHighlight) => {
    setTrimStart(h.start_time);
    setTrimEnd(h.end_time);
    if (h.suggested_theme && ["minimal", "blueprint", "anime", "ghibli", "papercut"].includes(h.suggested_theme)) {
      setTheme(h.suggested_theme as any);
    }
    if (h.suggested_caption_style && ["karaoke", "sentence"].includes(h.suggested_caption_style)) {
      setCaptionStyle(h.suggested_caption_style as any);
    }
    setSeekTime(h.start_time);
  };

  const handleUpdateCaption = (idx: number, newText: string) => {
    setCaptions((prev) => {
      const copy = [...prev];
      if (copy[idx]) {
        copy[idx] = { ...copy[idx], text: newText };
      }
      return copy;
    });
  };

  // Trigger FFmpeg Render
  const handleStartRender = async () => {
    setShowRenderModal(true);
    setRendering(true);
    try {
      const payload: RenderRequest = {
        start_time: trimStart,
        end_time: trimEnd,
        aspect_ratio: aspectRatio,
        theme,
        caption_style: captionStyle,
        captions: captions.filter((c) => c.start < trimEnd && c.end > trimStart),
      };

      const job = await apiFetch<RenderJobResponse>(`/projects/${id}/render`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setRenderJob(job);
      pollRenderStatus(job.render_id);
    } catch (err: any) {
      setRenderJob({
        render_id: "",
        status: "failed",
        progress: 0,
        error: err.message || "Failed to initiate rendering.",
      });
      setRendering(false);
    }
  };

  const pollRenderStatus = (renderId: string) => {
    stopRenderPolling();
    renderPollRef.current = setInterval(async () => {
      try {
        const statusRes = await apiFetch<RenderJobResponse>(`/projects/${id}/render/${renderId}/status`);
        setRenderJob(statusRes);
        if (statusRes.status === "completed" || statusRes.status === "failed") {
          setRendering(false);
          stopRenderPolling();
        }
      } catch (err: any) {
        setRenderJob((prev) => (prev ? { ...prev, status: "failed", error: err.message } : null));
        setRendering(false);
        stopRenderPolling();
      }
    }, 1500);
  };

  if (authLoading || (loading && !project)) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <p className="text-muted-foreground">Project not found or deleted.</p>
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-primary text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  const streamUrl = `http://localhost:8000/api/projects/${project.id}/video/stream`;
  const maxVideoDuration = project.video?.duration || 60;
  const cutDuration = Math.max(0, trimEnd - trimStart);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            aria-label="Back to dashboard"
            className="p-2 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-foreground">{project.title}</h1>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${
                  project.status === "completed"
                    ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800"
                    : project.status === "processing"
                    ? "bg-amber-950/60 text-amber-300 border border-amber-800 animate-pulse"
                    : project.status === "failed"
                    ? "bg-red-950/60 text-red-300 border border-red-800"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {project.status.toUpperCase()}
              </span>
            </div>
            {project.description && (
              <p className="text-xs text-muted-foreground mt-0.5">{project.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {project.status === "completed" && (
            <>
              <button
                onClick={() => setShowExportModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card text-xs font-semibold hover:bg-muted transition-colors"
              >
                <FileJson className="w-3.5 h-3.5" />
                Export Transcript
              </button>

              <button
                onClick={handleStartRender}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity shadow-md"
              >
                <Film className="w-4 h-4" />
                Export Final Video ({aspectRatio})
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div role="alert" className="flex items-center gap-2 p-3 text-sm rounded-lg bg-red-950/50 border border-red-800 text-red-200">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Case 1: No video uploaded yet */}
      {!project.video && project.status === "created" && (
        <div className="py-12">
          <VideoUploader projectId={project.id} onUploadComplete={handleUploadDone} />
        </div>
      )}

      {/* Case 2: Processing in progress */}
      {project.status === "processing" && (
        <div className="text-center py-20 px-4 rounded-xl border border-border bg-card/40 space-y-4 max-w-lg mx-auto">
          <div className="p-4 rounded-full bg-primary/10 text-primary w-fit mx-auto animate-spin">
            <RefreshCw className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">AI Video Transcription in Progress</h2>
            <p className="text-xs text-muted-foreground">
              Extracting speech audio, detecting pauses, and transcribing word timestamps via faster-whisper on CPU.
            </p>
          </div>
        </div>
      )}

      {/* Case 3: Processing failed */}
      {project.status === "failed" && (
        <div className="text-center py-16 px-4 rounded-xl border border-red-900/50 bg-red-950/20 space-y-4 max-w-lg mx-auto">
          <div className="p-3 rounded-full bg-red-900/50 text-red-400 w-fit mx-auto">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-red-200">Analysis Failed</h2>
            <p className="text-xs text-red-300">
              {transcript?.error_message || "An error occurred during audio extraction or transcription."}
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            {project.video && (
              <button
                onClick={handleRetry}
                disabled={retrying}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition-opacity"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Retry Now
              </button>
            )}
          </div>
        </div>
      )}

      {/* Case 4: Studio Workspace */}
      {project.status === "completed" && project.video && (
        <div className="space-y-6">
          {/* AI Viral Highlights Discovery Bar */}
          <div className="p-4 rounded-2xl border border-border bg-card/70 backdrop-blur shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
                  <Flame className="w-5 h-5 fill-current" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-foreground flex items-center gap-1.5">
                    AI Viral Scene Extractor
                    <span className="text-[10px] font-normal px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                      Gemini Powered
                    </span>
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Analyzes speech transcript to pick the top 30-60s retention hooks (no visual scene detection).
                  </p>
                </div>
              </div>

              <button
                onClick={handleFindViralClips}
                disabled={loadingHighlights}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-bold hover:opacity-95 disabled:opacity-50 transition-all shadow-sm shrink-0"
              >
                {loadingHighlights ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing Hook Potential...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    {highlights.length > 0 ? "Re-scan Viral Hooks" : "Find Viral Hooks"}
                  </>
                )}
              </button>
            </div>

            {highlightError && (
              <div className="text-xs text-red-400 bg-red-950/40 p-2 rounded-lg border border-red-900/60">
                {highlightError}
              </div>
            )}

            {/* Render Highlight Cards if found */}
            {highlights.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                {highlights.map((h, i) => {
                  const isCurrent = trimStart === h.start_time && trimEnd === h.end_time;
                  return (
                    <div
                      key={i}
                      className={`p-3 rounded-xl border transition-all text-xs flex flex-col justify-between space-y-2 ${
                        isCurrent
                          ? "border-amber-500 bg-amber-500/10 shadow-sm"
                          : "border-border bg-card/40 hover:bg-card"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-bold text-[10px]">
                            <Flame className="w-3 h-3 fill-current" />
                            {h.viral_score}% Score
                          </span>
                          <span className="font-mono text-muted-foreground text-[10px]">
                            {(h.end_time - h.start_time).toFixed(1)}s
                          </span>
                        </div>
                        <h4 className="font-bold text-foreground text-xs line-clamp-1">{h.hook_title}</h4>
                        <p className="text-muted-foreground text-[11px] line-clamp-2">{h.reasoning}</p>
                      </div>

                      <button
                        onClick={() => applyHighlight(h)}
                        className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
                          isCurrent
                            ? "bg-amber-500 text-black font-bold"
                            : "bg-secondary text-foreground hover:bg-secondary/80"
                        }`}
                      >
                        {isCurrent ? <Check className="w-3.5 h-3.5" /> : <Scissors className="w-3.5 h-3.5" />}
                        {isCurrent ? "Applied to Cut" : "Apply to Studio"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Studio Main Workspace Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Live Studio Video Preview */}
            <div className="lg:col-span-5 flex flex-col items-center space-y-4">
              <StudioPlayer
                src={streamUrl}
                currentTime={currentTime}
                onTimeUpdate={setCurrentTime}
                seekTime={seekTime}
                aspectRatio={aspectRatio}
                theme={theme}
                captionStyle={captionStyle}
                captions={captions}
                trimStart={trimStart}
                trimEnd={trimEnd}
                loopTrim={false}
              />
            </div>

            {/* Right Column: Studio Controls & Interactive Editors */}
            <div className="lg:col-span-7 space-y-4">
              {/* Studio Options Card: Aspect Ratio, Theme, Caption Style, Trim Bar */}
              <div className="p-4 rounded-2xl border border-border bg-card space-y-4 shadow-sm text-xs">
                {/* Row 1: Aspect Ratio & Caption Style */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Aspect Ratio Switcher */}
                  <div className="space-y-1.5">
                    <label className="font-semibold text-foreground flex items-center gap-1.5">
                      <Smartphone className="w-3.5 h-3.5 text-primary" />
                      Aspect Ratio Format
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setAspectRatio("9:16")}
                        className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-2 font-semibold transition-all ${
                          aspectRatio === "9:16"
                            ? "border-primary bg-primary text-primary-foreground shadow"
                            : "border-border bg-secondary/50 text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <Smartphone className="w-4 h-4" />
                        <span>9:16 Vertical (Shorts)</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setAspectRatio("16:9")}
                        className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-2 font-semibold transition-all ${
                          aspectRatio === "16:9"
                            ? "border-primary bg-primary text-primary-foreground shadow"
                            : "border-border bg-secondary/50 text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <Monitor className="w-4 h-4" />
                        <span>16:9 Landscape</span>
                      </button>
                    </div>
                  </div>

                  {/* Caption Animation Style (User requested choice) */}
                  <div className="space-y-1.5">
                    <label className="font-semibold text-foreground flex items-center gap-1.5">
                      <Type className="w-3.5 h-3.5 text-primary" />
                      Caption Animation Style
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setCaptionStyle("karaoke")}
                        className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-2 font-semibold transition-all ${
                          captionStyle === "karaoke"
                            ? "border-primary bg-primary text-primary-foreground shadow"
                            : "border-border bg-secondary/50 text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Word Karaoke</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setCaptionStyle("sentence")}
                        className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-2 font-semibold transition-all ${
                          captionStyle === "sentence"
                            ? "border-primary bg-primary text-primary-foreground shadow"
                            : "border-border bg-secondary/50 text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Sentence Card</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Row 2: Theme Selector */}
                <div className="space-y-1.5 pt-1">
                  <label className="font-semibold text-foreground flex items-center gap-1.5">
                    <Palette className="w-3.5 h-3.5 text-primary" />
                    Visual Theme & Grading
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                    {[
                      { id: "anime", label: "Anime Pop", desc: "Neon & Vibrant" },
                      { id: "blueprint", label: "Blueprint", desc: "Cyan Grid & Mono" },
                      { id: "ghibli", label: "Ghibli", desc: "Warm Golden Film" },
                      { id: "papercut", label: "Paper Cut", desc: "Clean Card Pill" },
                      { id: "minimal", label: "Minimal", desc: "Bold Contrast" },
                    ].map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setTheme(t.id as any)}
                        className={`p-2.5 rounded-xl border text-left transition-all ${
                          theme === t.id
                            ? "border-primary bg-primary/10 text-foreground ring-1 ring-primary"
                            : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                        }`}
                      >
                        <div className="font-bold text-xs">{t.label}</div>
                        <div className="text-[10px] text-muted-foreground truncate">{t.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Row 3: Manual Trim Sliders & Fine-Tuning */}
                <div className="space-y-2 pt-2 border-t border-border">
                  <div className="flex items-center justify-between">
                    <label className="font-semibold text-foreground flex items-center gap-1.5">
                      <Scissors className="w-3.5 h-3.5 text-primary" />
                      Manual Cut Boundaries
                    </label>
                    <span className="font-mono text-xs text-primary font-bold">
                      Duration: {cutDuration.toFixed(1)}s (Max {maxVideoDuration.toFixed(0)}s)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {/* Start Time Control */}
                    <div className="p-2.5 rounded-xl border border-border bg-secondary/30 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Cut Start</span>
                        <span className="font-mono font-bold text-foreground">{trimStart.toFixed(1)}s</span>
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={Math.max(0, trimEnd - 5)}
                        step={0.5}
                        value={trimStart}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value);
                          setTrimStart(val);
                          setSeekTime(val);
                        }}
                        className="w-full accent-primary cursor-pointer"
                      />
                      <div className="flex gap-1.5">
                        <button
                          type="button"
                          onClick={() => setTrimStart((p) => Math.max(0, p - 1))}
                          className="flex-1 py-0.5 rounded bg-card border border-border text-[10px] hover:bg-muted"
                        >
                          -1s
                        </button>
                        <button
                          type="button"
                          onClick={() => setTrimStart((p) => Math.min(trimEnd - 5, p + 1))}
                          className="flex-1 py-0.5 rounded bg-card border border-border text-[10px] hover:bg-muted"
                        >
                          +1s
                        </button>
                      </div>
                    </div>

                    {/* End Time Control */}
                    <div className="p-2.5 rounded-xl border border-border bg-secondary/30 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Cut End</span>
                        <span className="font-mono font-bold text-foreground">{trimEnd.toFixed(1)}s</span>
                      </div>
                      <input
                        type="range"
                        min={trimStart + 5}
                        max={maxVideoDuration}
                        step={0.5}
                        value={trimEnd}
                        onChange={(e) => setTrimEnd(parseFloat(e.target.value))}
                        className="w-full accent-primary cursor-pointer"
                      />
                      <div className="flex gap-1.5">
                        <button
                          type="button"
                          onClick={() => setTrimEnd((p) => Math.max(trimStart + 5, p - 1))}
                          className="flex-1 py-0.5 rounded bg-card border border-border text-[10px] hover:bg-muted"
                        >
                          -1s
                        </button>
                        <button
                          type="button"
                          onClick={() => setTrimEnd((p) => Math.min(maxVideoDuration, p + 1))}
                          className="flex-1 py-0.5 rounded bg-card border border-border text-[10px] hover:bg-muted"
                        >
                          +1s
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Multi-Tab Workspace Panel */}
              <div className="h-[460px] flex flex-col bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
                {/* Tabs Header */}
                <div className="flex items-center border-b border-border bg-card/80 p-1.5 gap-1 text-xs">
                  <button
                    onClick={() => setActiveTab("subtitles")}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-xl font-medium transition-colors ${
                      activeTab === "subtitles"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    <Type className="w-3.5 h-3.5" />
                    <span>Live Caption Editor</span>
                  </button>

                  <button
                    onClick={() => setActiveTab("transcript")}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-xl font-medium transition-colors ${
                      activeTab === "transcript"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Full Transcript</span>
                  </button>

                  <button
                    onClick={() => setActiveTab("scenes")}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-xl font-medium transition-colors ${
                      activeTab === "scenes"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>Keyframes & Silence</span>
                  </button>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-hidden p-2">
                  {activeTab === "subtitles" && (
                    <CaptionEditor
                      captions={captions}
                      onUpdateCaption={handleUpdateCaption}
                      trimStart={trimStart}
                      trimEnd={trimEnd}
                      currentTime={currentTime}
                      onSeek={(s) => setSeekTime(s)}
                    />
                  )}

                  {activeTab === "transcript" && (
                    <div className="h-full">
                      <TranscriptViewer
                        segments={transcript?.transcript_json?.segments || []}
                        currentTime={currentTime}
                        onSeek={(s) => setSeekTime(s)}
                      />
                    </div>
                  )}

                  {activeTab === "scenes" && (
                    <div className="h-full overflow-y-auto p-3 space-y-4 text-xs">
                      {/* Silence Intervals */}
                      {analysis?.silence_intervals && analysis.silence_intervals.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="font-semibold text-foreground flex items-center gap-1.5">
                            <VolumeX className="w-3.5 h-3.5 text-primary" />
                            Detected Silence Pauses ({analysis.silence_intervals.length})
                          </h4>
                          <div className="grid grid-cols-2 gap-2">
                            {analysis.silence_intervals.slice(0, 8).map((sil, i) => (
                              <button
                                key={i}
                                onClick={() => setSeekTime(sil.start)}
                                className="p-2 rounded-lg border border-border bg-secondary/30 text-left hover:bg-secondary/60"
                              >
                                <span className="font-mono text-primary font-bold">
                                  {sil.start.toFixed(1)}s - {sil.end.toFixed(1)}s
                                </span>
                                <div className="text-[10px] text-muted-foreground">Pause: {sil.duration.toFixed(1)}s</div>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Frames */}
                      {analysis?.frames && analysis.frames.length > 0 && (
                        <div className="space-y-2 pt-2">
                          <h4 className="font-semibold text-foreground flex items-center gap-1.5">
                            <Film className="w-3.5 h-3.5 text-primary" />
                            Keyframe Thumbnails
                          </h4>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            {analysis.frames.map((frame, i) => (
                              <div
                                key={i}
                                onClick={() => setSeekTime(frame.timestamp)}
                                className="rounded-lg overflow-hidden border border-border bg-black cursor-pointer group relative"
                              >
                                {frame.url && (
                                  <img
                                    src={`http://localhost:8000${frame.url}`}
                                    alt={`Frame ${frame.timestamp}s`}
                                    className="w-full aspect-video object-cover group-hover:opacity-80 transition-opacity"
                                  />
                                )}
                                <div className="absolute bottom-1 left-1 bg-black/70 px-1.5 py-0.5 rounded text-[10px] font-mono text-white">
                                  {frame.timestamp.toFixed(1)}s
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Render Modal */}
      <RenderModal
        isOpen={showRenderModal}
        onClose={() => setShowRenderModal(false)}
        renderJob={renderJob}
        rendering={rendering}
      />

      {/* JSON/SRT Export Modal */}
      <JsonExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        projectId={project.id}
        jsonData={transcript?.transcript_json || {}}
      />
    </div>
  );
}
