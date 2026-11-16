"use client";

import { useState } from "react";
import { Copy, Check, Download, X, FileJson, FileText } from "lucide-react";

interface JsonExportModalProps {
  projectId: string;
  jsonData: any;
  isOpen: boolean;
  onClose: () => void;
}

export function JsonExportModal({ projectId, jsonData, isOpen, onClose }: JsonExportModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const jsonString = JSON.stringify(jsonData, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (format: "json" | "srt" | "vtt") => {
    const token = localStorage.getItem("clipforge_token");
    const url = `http://localhost:8000/api/projects/${projectId}/transcript/export?format=${format}`;
    
    // Trigger browser download via fetch with bearer token
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => res.blob())
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `transcript.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch(() => alert("Export failed"));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-card border border-border rounded-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileJson className="w-5 h-5 text-primary" />
            <h2 className="font-bold text-base text-foreground">Timestamped Transcript JSON</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden p-4 bg-background">
          <pre className="h-full overflow-auto p-4 rounded-lg bg-card border border-border font-mono text-xs text-foreground/90 selection:bg-primary/30">
            {jsonString}
          </pre>
        </div>

        <div className="p-4 border-t border-border bg-card/60 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDownload("json")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Download .JSON
            </button>
            <button
              onClick={() => handleDownload("srt")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80 transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              Download .SRT
            </button>
            <button
              onClick={() => handleDownload("vtt")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80 transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              Download .VTT
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 transition-opacity"
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied to Clipboard!" : "Copy JSON"}
          </button>
        </div>
      </div>
    </div>
  );
}
