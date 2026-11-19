"use client";

import { useState, useRef } from "react";
import { UploadCloud, FileVideo, AlertCircle, Loader2, Youtube, ArrowRight, Sparkles } from "lucide-react";
import { importYouTubeVideo } from "@/lib/api";

interface VideoUploaderProps {
  projectId: string;
  onUploadComplete: () => void;
}

export function VideoUploader({ projectId, onUploadComplete }: VideoUploaderProps) {
  const [activeTab, setActiveTab] = useState<"file" | "youtube">("youtube");
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // YouTube Link State
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [importingYt, setImportingYt] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  };

  const validateAndUpload = async (file: File) => {
    setError(null);
    const validExtensions = [".mp4", ".mov", ".webm", ".mkv"];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExt && !file.type.startsWith("video/")) {
      setError("Please select a supported video format: MP4, MOV, WebM, or MKV.");
      return;
    }

    setUploading(true);
    setProgress(10);

    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("clipforge_token");
    const xhr = new XMLHttpRequest();

    xhr.open("POST", `http://localhost:8000/api/projects/${projectId}/upload`);
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 90);
        setProgress(Math.max(10, percent));
      }
    };

    xhr.onload = () => {
      setUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(100);
        onUploadComplete();
      } else {
        try {
          const res = JSON.parse(xhr.responseText);
          setError(res?.detail?.error?.message || "Upload failed.");
        } catch {
          setError("Upload failed. Please try again.");
        }
      }
    };

    xhr.onerror = () => {
      setUploading(false);
      setError("Network error occurred during upload.");
    };

    xhr.send(formData);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const handleYouTubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = youtubeUrl.trim();
    if (!trimmed) {
      setError("Please enter a YouTube video or live stream URL.");
      return;
    }

    const isYt = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|live\/|shorts\/)|youtu\.be\/)[\w\-]+/i.test(trimmed);
    if (!isYt) {
      setError("Please enter a valid YouTube URL (e.g. https://www.youtube.com/watch?v=... or https://youtube.com/live/...).");
      return;
    }

    setImportingYt(true);
    try {
      await importYouTubeVideo(projectId, trimmed);
      onUploadComplete();
    } catch (err: any) {
      setError(err.message || "Failed to import YouTube video.");
      setImportingYt(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {/* Ingestion Source Switcher Tabs */}
      <div className="flex items-center p-1.5 rounded-2xl bg-card border border-border shadow-sm">
        <button
          type="button"
          onClick={() => setActiveTab("youtube")}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold transition-all ${
            activeTab === "youtube"
              ? "bg-red-600 text-white shadow-md shadow-red-900/30"
              : "text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          <Youtube className="w-4 h-4 fill-current" />
          <span>Import YouTube / Live Stream</span>
          <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded font-normal">Auto 30s Clips</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("file")}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold transition-all ${
            activeTab === "file"
              ? "bg-primary text-primary-foreground shadow-md"
              : "text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          <FileVideo className="w-4 h-4" />
          <span>Upload Local File</span>
        </button>
      </div>

      {error && (
        <div role="alert" className="flex items-center gap-2 p-3 text-sm rounded-lg bg-red-950/50 border border-red-800 text-red-200">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tab 1: YouTube / Live Stream Importer */}
      {activeTab === "youtube" && (
        <div className="p-8 rounded-2xl border border-border bg-card/60 backdrop-blur shadow-sm space-y-5 text-center">
          <div className="p-4 rounded-full bg-red-600/10 text-red-500 w-fit mx-auto border border-red-500/20">
            <Youtube className="w-8 h-8 fill-current" />
          </div>

          <div className="space-y-1.5">
            <h3 className="font-bold text-base text-foreground">Import YouTube Video or Live Stream</h3>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              Paste any YouTube video or completed live stream link. Our pipeline will download, mux audio, transcribe, and automatically generate <strong className="text-foreground">multiple 30-second viral Shorts</strong>.
            </p>
          </div>

          <form onSubmit={handleYouTubeSubmit} className="space-y-3 max-w-lg mx-auto">
            <div className="relative">
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=... or https://youtube.com/live/..."
                disabled={importingYt}
                className="w-full pl-4 pr-12 py-3 rounded-xl border border-input bg-background/80 text-foreground text-xs placeholder:text-muted-foreground focus:ring-2 focus:ring-red-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={importingYt || !youtubeUrl.trim()}
              className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 text-white text-xs font-bold hover:opacity-95 disabled:opacity-50 transition-all shadow-md shadow-red-950/40"
            >
              {importingYt ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting to YouTube Stream...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Import & Generate Viral Highlights
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="flex items-center justify-center gap-4 text-[11px] text-muted-foreground pt-1">
            <span>✓ Up to 1080p resolution</span>
            <span>•</span>
            <span>✓ Auto audio muxing</span>
            <span>•</span>
            <span>✓ AI Viral Highlights</span>
          </div>
        </div>
      )}

      {/* Tab 2: Local File Dropzone */}
      {activeTab === "file" && (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-3 ${
            isDragging
              ? "border-primary bg-primary/10 scale-[1.01]"
              : "border-border hover:border-primary/50 bg-card/40"
          } ${uploading ? "pointer-events-none opacity-80" : ""}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/quicktime,video/webm,video/x-matroska"
            className="hidden"
            onChange={handleFileChange}
          />

          <div className="p-4 rounded-full bg-primary/10 text-primary">
            <UploadCloud className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <p className="font-semibold text-base text-foreground">
              {uploading ? "Uploading video..." : "Drag and drop your raw footage here"}
            </p>
            <p className="text-xs text-muted-foreground">
              Supports MP4, MOV, WebM, and MKV (No file size limit)
            </p>
          </div>

          {uploading ? (
            <div className="w-full max-w-xs space-y-2 mt-3">
              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary h-2 transition-all duration-300 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">{progress}% uploaded</p>
            </div>
          ) : (
            <button
              type="button"
              className="mt-2 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground text-xs font-semibold transition-colors"
            >
              <FileVideo className="w-4 h-4" />
              Browse Local Files
            </button>
          )}
        </div>
      )}
    </div>
  );
}
