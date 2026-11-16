"use client";

import { Clock, Edit3, MessageSquare } from "lucide-react";
import { RenderCaptionItem } from "@/lib/api";

interface CaptionEditorProps {
  captions: RenderCaptionItem[];
  onUpdateCaption: (index: number, newText: string) => void;
  trimStart: number;
  trimEnd: number;
  currentTime: number;
  onSeek: (seconds: number) => void;
}

export function CaptionEditor({
  captions,
  onUpdateCaption,
  trimStart,
  trimEnd,
  currentTime,
  onSeek,
}: CaptionEditorProps) {
  // Filter captions that overlap with the active cut range
  const activeCaptions = captions
    .map((c, originalIdx) => ({ ...c, originalIdx }))
    .filter((c) => c.start < trimEnd && c.end > trimStart);

  if (activeCaptions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground space-y-2">
        <MessageSquare className="w-8 h-8 opacity-40" />
        <p className="text-xs">No speech segments detected inside this trimmed range.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-3 overflow-y-auto max-h-[500px]">
      <div className="flex items-center justify-between pb-1 border-b border-border text-xs text-muted-foreground font-medium">
        <span>Active Cut Captions ({activeCaptions.length})</span>
        <span>Click text to edit</span>
      </div>

      <div className="space-y-2">
        {activeCaptions.map((cap) => {
          const isActive = currentTime >= cap.start && currentTime <= cap.end;
          return (
            <div
              key={cap.originalIdx}
              className={`p-3 rounded-xl border transition-all text-xs space-y-2 ${
                isActive
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-border bg-card/60 hover:bg-card"
              }`}
            >
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => onSeek(cap.start)}
                  className="inline-flex items-center gap-1 font-mono text-[11px] text-primary hover:underline"
                  title="Click to seek"
                >
                  <Clock className="w-3 h-3" />
                  <span>
                    {cap.start.toFixed(1)}s - {cap.end.toFixed(1)}s
                  </span>
                </button>
                <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                  <Edit3 className="w-3 h-3" />
                  <span>Editable</span>
                </div>
              </div>

              <textarea
                value={cap.text}
                onChange={(e) => onUpdateCaption(cap.originalIdx, e.target.value)}
                rows={2}
                className="w-full bg-background/80 border border-input rounded-lg p-2 text-foreground text-xs focus:ring-1 focus:ring-primary focus:outline-none resize-none"
                placeholder="Caption text..."
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
