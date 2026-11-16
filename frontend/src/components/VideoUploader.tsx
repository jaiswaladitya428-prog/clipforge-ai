"use client";

import { useState, useRef } from "react";
import { UploadCloud, FileVideo, AlertCircle, Loader2 } from "lucide-react";

interface VideoUploaderProps {
  projectId: string;
  onUploadComplete: () => void;
}

export function VideoUploader({ projectId, onUploadComplete }: VideoUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
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

    if (file.size > 500 * 1024 * 1024) {
      setError("File exceeds 500 MB limit.");
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

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {error && (
        <div role="alert" className="flex items-center gap-2 p-3 text-sm rounded-lg bg-red-950/50 border border-red-800 text-red-200">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-3 ${
          isDragging
            ? "border-primary bg-primary/10 scale-[1.01]"
            : "border-border hover:border-primary/50 bg-card/30"
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
            Supports MP4, MOV, WebM, and MKV up to 500 MB
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
            className="mt-2 inline-flex items-center gap-2 px-4 py-2 rounded-md bg-secondary hover:bg-secondary/80 text-foreground text-xs font-medium transition-colors"
          >
            <FileVideo className="w-4 h-4" />
            Browse Files
          </button>
        )}
      </div>
    </div>
  );
}
