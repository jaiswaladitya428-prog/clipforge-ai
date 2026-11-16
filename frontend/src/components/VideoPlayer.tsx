"use client";

import { useRef, useEffect } from "react";

interface VideoPlayerProps {
  src: string;
  onTimeUpdate?: (currentTime: number) => void;
  seekTime?: number | null;
}

export function VideoPlayer({ src, onTimeUpdate, seekTime }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (seekTime !== null && seekTime !== undefined && videoRef.current) {
      videoRef.current.currentTime = seekTime;
      videoRef.current.play().catch(() => {});
    }
  }, [seekTime]);

  const handleTimeUpdate = () => {
    if (videoRef.current && onTimeUpdate) {
      onTimeUpdate(videoRef.current.currentTime);
    }
  };

  return (
    <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-border shadow-md">
      <video
        ref={videoRef}
        src={src}
        controls
        playsInline
        onTimeUpdate={handleTimeUpdate}
        className="w-full h-full object-contain"
      />
    </div>
  );
}
