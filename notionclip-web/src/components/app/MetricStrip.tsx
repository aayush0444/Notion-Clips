"use client"

import { useAppStore } from "@/lib/store"

export function MetricStrip() {
  const { results, mode, processingTime, wordCount, duration, transcriptFetchMs, extractMs, transcriptCacheHit, extractCacheHit } = useAppStore()
  if (!results) return null

  const keyPoints =
    mode === "study"
      ? results.key_facts?.length || 0
      : mode === "work"
        ? results.key_points?.length || 0
        : results.key_takeaways?.length || 0

  const durationLabel = duration && duration > 0 ? `${Math.round(duration)} min` : "—"

  const stats = [
    { label: "Processing Time", value: processingTime ? `${(processingTime / 1000).toFixed(1)}s` : "0s" },
    { label: "Transcript Fetch", value: transcriptFetchMs ? `${(transcriptFetchMs / 1000).toFixed(1)}s${transcriptCacheHit ? " (cache)" : ""}` : "—" },
    { label: "AI Extraction", value: extractMs ? `${(extractMs / 1000).toFixed(1)}s${extractCacheHit ? " (cache)" : ""}` : "—" },
    { label: "Video Length", value: durationLabel },
    { label: "Word Count", value: wordCount ? wordCount.toLocaleString() : "0" },
    { label: "Key Points", value: `${keyPoints}` },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 pt-4 border-t border-border/70">
      {stats.map((item) => (
        <div key={item.label} className="bg-card rounded-lg p-3 border border-border shadow-[0_4px_16px_rgba(61,36,102,0.08)]">
          <div className="text-xs app-text-muted mb-1">{item.label}</div>
          <div className="text-sm text-foreground">{item.value}</div>
        </div>
      ))}
    </div>
  )
}
