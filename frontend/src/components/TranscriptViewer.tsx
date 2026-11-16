"use client";

import { useEffect, useRef, useState } from "react";
import { TranscriptSegment } from "@/lib/api";
import { Search, Play, Clock } from "lucide-react";

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  currentTime: number;
  onSeek: (seconds: number) => void;
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms}`;
}

export function TranscriptViewer({ segments, currentTime, onSeek }: TranscriptViewerProps) {
  const [filter, setFilter] = useState("");
  const activeSegmentRef = useRef<HTMLDivElement>(null);

  const activeIndex = segments.findIndex(
    (seg) => currentTime >= seg.start && currentTime <= seg.end
  );

  useEffect(() => {
    if (activeSegmentRef.current) {
      activeSegmentRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [activeIndex]);

  const filteredSegments = filter.trim()
    ? segments.filter((s) => s.text.toLowerCase().includes(filter.toLowerCase()))
    : segments;

  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-xl overflow-hidden shadow-sm">
      <div className="p-3 border-b border-border bg-card/60 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
          <Clock className="w-4 h-4 text-primary" />
          <span>Timestamped Transcript</span>
          <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[10px] font-mono">
            {segments.length} segments
          </span>
        </div>

        <div className="relative w-44">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search transcript..."
            className="w-full pl-8 pr-2.5 py-1 text-xs rounded-md bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-[500px]">
        {filteredSegments.length === 0 ? (
          <p className="text-center py-8 text-xs text-muted-foreground">No matching transcript segments found.</p>
        ) : (
          filteredSegments.map((segment) => {
            const isActive = segment.id === segments[activeIndex]?.id;
            return (
              <div
                key={segment.id}
                ref={isActive ? activeSegmentRef : null}
                onClick={() => onSeek(segment.start)}
                className={`group p-2.5 rounded-lg border transition-all cursor-pointer flex flex-col gap-1.5 ${
                  isActive
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "border-transparent hover:border-border hover:bg-muted/40"
                }`}
              >
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span
                    className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${
                      isActive ? "bg-primary text-primary-foreground font-semibold" : "bg-muted text-muted-foreground group-hover:text-foreground"
                    }`}
                  >
                    <Play className="w-2.5 h-2.5" />
                    {formatTime(segment.start)} - {formatTime(segment.end)}
                  </span>
                </div>

                <p className={`text-xs leading-relaxed ${isActive ? "text-foreground font-medium" : "text-muted-foreground"}`}>
                  {segment.text}
                </p>

                {/* Word level timestamps preview on active segment */}
                {isActive && segment.words && segment.words.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1 border-t border-primary/20">
                    {segment.words.map((w, idx) => {
                      const isWordActive = currentTime >= w.start && currentTime <= w.end;
                      return (
                        <span
                          key={idx}
                          onClick={(e) => {
                            e.stopPropagation();
                            onSeek(w.start);
                          }}
                          className={`text-[10px] px-1 py-0.5 rounded cursor-pointer transition-colors ${
                            isWordActive
                              ? "bg-primary text-primary-foreground font-bold"
                              : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          {w.word}
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
