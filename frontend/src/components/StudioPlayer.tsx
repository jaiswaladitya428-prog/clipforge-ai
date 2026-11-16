"use client";

import { useRef, useEffect, useState } from "react";
import { Play, Pause, RotateCcw, Smartphone, Monitor } from "lucide-react";
import { RenderCaptionItem } from "@/lib/api";

interface StudioPlayerProps {
  src: string;
  currentTime?: number;
  onTimeUpdate?: (currentTime: number) => void;
  seekTime?: number | null;
  aspectRatio: "9:16" | "16:9";
  theme: "minimal" | "blueprint" | "anime" | "ghibli" | "papercut";
  captionStyle: "karaoke" | "sentence";
  captions: RenderCaptionItem[];
  trimStart: number;
  trimEnd: number;
  loopTrim?: boolean;
}

// Guaranteed browser-native CSS filters (immune to Tailwind class purging)
const THEME_CSS_FILTERS: Record<string, string> = {
  minimal: "contrast(1.08) saturate(1.05)",
  blueprint: "grayscale(0.4) hue-rotate(185deg) contrast(1.35) saturate(2.2) brightness(0.92)",
  anime: "contrast(1.25) saturate(1.65) brightness(1.05)",
  ghibli: "sepia(0.35) contrast(1.1) brightness(1.03) saturate(1.25)",
  papercut: "contrast(1.25) saturate(0.85) brightness(1.02)",
};

export function StudioPlayer({
  src,
  onTimeUpdate,
  seekTime,
  aspectRatio,
  theme,
  captionStyle,
  captions,
  trimStart,
  trimEnd,
  loopTrim = false,
}: StudioPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSec, setCurrentSec] = useState(0);

  useEffect(() => {
    if (seekTime !== null && seekTime !== undefined && videoRef.current) {
      videoRef.current.currentTime = seekTime;
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  }, [seekTime]);

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const t = videoRef.current.currentTime;
    setCurrentSec(t);
    if (onTimeUpdate) onTimeUpdate(t);

    if (loopTrim && (t >= trimEnd || t < trimStart)) {
      videoRef.current.currentTime = trimStart;
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      if (videoRef.current.currentTime < trimStart || videoRef.current.currentTime >= trimEnd) {
        videoRef.current.currentTime = trimStart;
      }
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleSeekStart = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = trimStart;
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  // Find active caption segment
  const activeCaption = captions.find(
    (c) => currentSec >= c.start && currentSec <= c.end
  );

  const activeFilter = THEME_CSS_FILTERS[theme] || "none";

  return (
    <div className="flex flex-col items-center w-full space-y-3">
      {/* Container Frame */}
      <div
        className={`relative overflow-hidden bg-black rounded-2xl border-2 border-border shadow-2xl transition-all duration-300 ${
          aspectRatio === "9:16"
            ? "w-[300px] h-[533px] sm:w-[340px] sm:h-[604px] max-w-full"
            : "w-full aspect-video"
        }`}
      >
        {/* Background Blurred Fill for 9:16 Vertical */}
        {aspectRatio === "9:16" && (
          <video
            src={src}
            muted
            playsInline
            style={{ filter: `${activeFilter} blur(24px)` }}
            className="absolute inset-0 w-full h-full object-cover opacity-60 scale-125 pointer-events-none"
            tabIndex={-1}
          />
        )}

        {/* Blueprint Grid Overlay */}
        {theme === "blueprint" && (
          <div className="absolute inset-0 pointer-events-none z-10 opacity-30 bg-[radial-gradient(#00E5FF_1.5px,transparent_1.5px)] [background-size:20px_20px]" />
        )}

        {/* Paper Cut Border Overlay */}
        {theme === "papercut" && (
          <div className="absolute inset-3 rounded-2xl border-2 border-white/40 pointer-events-none z-10 shadow-[inset_0_0_25px_rgba(0,0,0,0.6)]" />
        )}

        {/* Anime Glow Accent Overlay */}
        {theme === "anime" && (
          <div className="absolute inset-0 pointer-events-none z-10 opacity-25 bg-gradient-to-t from-purple-900/40 via-transparent to-pink-900/30 mix-blend-overlay" />
        )}

        {/* Ghibli Warm Tone Overlay */}
        {theme === "ghibli" && (
          <div className="absolute inset-0 pointer-events-none z-10 opacity-20 bg-amber-500/15 mix-blend-soft-light" />
        )}

        {/* Main Video Stream */}
        <video
          ref={videoRef}
          src={src}
          playsInline
          onTimeUpdate={handleTimeUpdate}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onClick={togglePlay}
          style={{ filter: activeFilter }}
          className="relative z-0 w-full h-full object-contain cursor-pointer transition-all duration-300"
        />

        {/* Live Synchronized Themed Subtitle Overlay */}
        {activeCaption && (
          <div className="absolute bottom-10 inset-x-4 z-20 flex justify-center pointer-events-none text-center animate-in fade-in duration-150">
            {theme === "blueprint" ? (
              <div className="bg-[#001020]/90 border border-[#00E5FF] px-3.5 py-1.5 rounded-md font-mono text-[#00E5FF] text-xs sm:text-sm font-bold tracking-wider shadow-[0_0_15px_rgba(0,229,255,0.4)]">
                {activeCaption.text}
              </div>
            ) : theme === "anime" ? (
              <div className="px-3 py-1.5 font-black uppercase text-base sm:text-lg tracking-wider text-[#FFE600] drop-shadow-[0_2px_4px_#FF0055]">
                {captionStyle === "karaoke" && activeCaption.words && activeCaption.words.length > 0 ? (
                  <span className="flex flex-wrap justify-center gap-1.5">
                    {activeCaption.words.map((w, idx) => {
                      const isWordActive = currentSec >= w.start && currentSec <= w.end;
                      return (
                        <span
                          key={idx}
                          className={`transition-all duration-100 ${
                            isWordActive
                              ? "text-white scale-125 drop-shadow-[0_0_12px_#FFE600]"
                              : "text-[#FFE600]"
                          }`}
                        >
                          {w.word}
                        </span>
                      );
                    })}
                  </span>
                ) : (
                  <span>{activeCaption.text}</span>
                )}
              </div>
            ) : theme === "ghibli" ? (
              <div className="bg-black/50 backdrop-blur-sm px-4 py-2 rounded-full font-serif text-[#FFF8E7] text-xs sm:text-sm shadow-md italic border border-[#FFF8E7]/20">
                {activeCaption.text}
              </div>
            ) : theme === "papercut" ? (
              <div className="bg-white/95 text-zinc-900 px-4 py-1.5 rounded-lg font-sans font-extrabold text-xs sm:text-sm shadow-2xl border border-zinc-200">
                {activeCaption.text}
              </div>
            ) : (
              // Minimal
              <div className="bg-black/70 backdrop-blur-sm px-3.5 py-1.5 rounded-lg font-sans font-bold text-white text-xs sm:text-sm drop-shadow-md border border-white/10">
                {activeCaption.text}
              </div>
            )}
          </div>
        )}

        {/* Aspect Ratio Badge */}
        <div className="absolute top-3 right-3 z-20 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[11px] font-medium border border-white/10 pointer-events-none">
          {aspectRatio === "9:16" ? <Smartphone className="w-3 h-3" /> : <Monitor className="w-3 h-3" />}
          <span>{aspectRatio}</span>
        </div>

        {/* Current Theme Badge */}
        <div className="absolute top-3 left-3 z-20 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[10px] font-semibold uppercase tracking-wider border border-white/10 pointer-events-none">
          {theme}
        </div>
      </div>

      {/* Mini Player Controls Bar */}
      <div className="flex items-center justify-between w-full max-w-md px-3 py-1.5 rounded-xl border border-border bg-card/60 backdrop-blur text-xs">
        <button
          onClick={handleSeekStart}
          aria-label="Seek to start of clip"
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title="Jump to Start of Cut"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={togglePlay}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
          <span>{isPlaying ? "Pause Preview" : "Play Cut"}</span>
        </button>

        <div className="font-mono text-muted-foreground text-[11px]">
          {currentSec.toFixed(1)}s / {trimEnd.toFixed(1)}s
        </div>
      </div>
    </div>
  );
}
