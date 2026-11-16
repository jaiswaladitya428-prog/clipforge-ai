import Link from "next/link";
import { ArrowRight, FileJson, Clock, Cpu, ShieldCheck } from "lucide-react";

export default function Home() {
  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 py-16 text-center">
      <div className="max-w-3xl space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-card/80 text-xs font-medium text-muted-foreground">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          Powered by faster-whisper (CPU INT8 Optimized)
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-foreground">
          Transform Raw Video into <br />
          <span className="text-primary">Timestamped Transcripts</span>
        </h1>

        <p className="text-lg sm:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto">
          Upload any MP4, MOV, or WebM video. Our local AI pipeline extracts high-fidelity audio,
          detects speech using <code className="text-primary font-mono text-sm">faster-whisper</code>, and delivers word-level timestamped JSON with millisecond precision.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/register"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            Start Transcribing Free
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-lg border border-border bg-card font-medium text-foreground hover:bg-muted transition-colors"
          >
            Sign In to Dashboard
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mt-20 text-left">
        <div className="p-5 rounded-lg border border-border bg-card/40 space-y-2">
          <div className="p-2.5 rounded-md bg-primary/10 text-primary w-fit">
            <Clock className="w-5 h-5" />
          </div>
          <h2 className="font-semibold text-foreground text-base">Timestamped JSON</h2>
          <p className="text-xs text-muted-foreground leading-normal">
            Word-level and sentence-level start & end timestamps ready for programmatic video editing and subtitling.
          </p>
        </div>

        <div className="p-5 rounded-lg border border-border bg-card/40 space-y-2">
          <div className="p-2.5 rounded-md bg-primary/10 text-primary w-fit">
            <Cpu className="w-5 h-5" />
          </div>
          <h2 className="font-semibold text-foreground text-base">Lightweight CPU Run</h2>
          <p className="text-xs text-muted-foreground leading-normal">
            Optimized with INT8 quantization to run cleanly within 8 GB RAM on Windows 11 with no dedicated GPU required.
          </p>
        </div>

        <div className="p-5 rounded-lg border border-border bg-card/40 space-y-2">
          <div className="p-2.5 rounded-md bg-primary/10 text-primary w-fit">
            <FileJson className="w-5 h-5" />
          </div>
          <h2 className="font-semibold text-foreground text-base">Multi-Format Exports</h2>
          <p className="text-xs text-muted-foreground leading-normal">
            Export directly as structured JSON, standard SubRip (.srt), or WebVTT (.vtt) caption formats in one click.
          </p>
        </div>

        <div className="p-5 rounded-lg border border-border bg-card/40 space-y-2">
          <div className="p-2.5 rounded-md bg-primary/10 text-primary w-fit">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h2 className="font-semibold text-foreground text-base">Private & Self-Hosted</h2>
          <p className="text-xs text-muted-foreground leading-normal">
            All videos and transcripts remain on your local system with isolated per-user account authentication.
          </p>
        </div>
      </div>
    </div>
  );
}
