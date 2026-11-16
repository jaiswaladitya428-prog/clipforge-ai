"use client";

import { useState } from "react";
import { Download, CheckCircle, AlertCircle, Loader2, X, Sparkles, Film } from "lucide-react";
import { RenderJobResponse } from "@/lib/api";

interface RenderModalProps {
  isOpen: boolean;
  onClose: () => void;
  renderJob: RenderJobResponse | null;
  rendering: boolean;
}

export function RenderModal({ isOpen, onClose, renderJob, rendering }: RenderModalProps) {
  const [downloading, setDownloading] = useState(false);

  if (!isOpen) return null;

  const isCompleted = renderJob?.status === "completed" && renderJob.download_url;
  const isFailed = renderJob?.status === "failed";
  const downloadUrl = renderJob?.download_url ? `http://localhost:8000${renderJob.download_url}` : null;

  const handleDownload = async () => {
    if (!downloadUrl) return;
    setDownloading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("clipforge_token") : null;
      const res = await fetch(downloadUrl, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Download request failed");
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `clipforge_${renderJob?.render_id?.slice(0, 8) || "export"}.mp4`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 10000);
    } catch (err) {
      // Fallback to direct navigation if blob fails
      window.location.href = downloadUrl;
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Film className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Export Final Video</h2>
              <p className="text-xs text-muted-foreground">Native high-speed FFmpeg rendering</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content State: Rendering */}
        {rendering && !isCompleted && !isFailed && (
          <div className="py-8 text-center space-y-4">
            <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
              <Sparkles className="w-5 h-5 text-primary absolute animate-pulse" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-sm font-semibold text-foreground">Rendering with Local FFmpeg...</h3>
              <p className="text-xs text-muted-foreground max-w-xs mx-auto">
                Trimming clip, applying aspect ratio transform, theme color grades, and burning styled captions.
              </p>
            </div>
            {/* Progress Bar */}
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300 rounded-full"
                style={{ width: `${renderJob?.progress || 35}%` }}
              />
            </div>
            <div className="text-[11px] font-mono text-muted-foreground">
              Progress: {renderJob?.progress || 35}%
            </div>
          </div>
        )}

        {/* Content State: Completed */}
        {isCompleted && (
          <div className="py-6 text-center space-y-5">
            <div className="p-3 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800 w-fit mx-auto">
              <CheckCircle className="w-10 h-10" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-foreground">Your Video is Ready!</h3>
              <p className="text-xs text-muted-foreground">
                Rendered 100% locally with native FFmpeg in seconds.
              </p>
            </div>

            {/* Video Preview */}
            {downloadUrl && (
              <div className="rounded-xl overflow-hidden border border-border bg-black max-h-56">
                <video src={downloadUrl} controls playsInline className="w-full max-h-56 object-contain" />
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 rounded-lg border border-border text-xs font-medium hover:bg-muted transition-colors"
              >
                Close
              </button>
              {downloadUrl && (
                <button
                  onClick={handleDownload}
                  disabled={downloading}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 transition-opacity shadow disabled:opacity-50"
                >
                  {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  {downloading ? "Preparing..." : "Download MP4"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Content State: Failed */}
        {isFailed && (
          <div className="py-6 text-center space-y-4">
            <div className="p-3 rounded-full bg-red-950/60 text-red-400 border border-red-800 w-fit mx-auto">
              <AlertCircle className="w-10 h-10" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-red-200">Render Failed</h3>
              <p className="text-xs text-red-300 max-w-sm mx-auto">
                {renderJob?.error || "FFmpeg encountered an error during rendering."}
              </p>
            </div>
            <div className="pt-2">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80 transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
