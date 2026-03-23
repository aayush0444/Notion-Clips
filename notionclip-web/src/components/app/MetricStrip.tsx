"use client"

import { useAppStore } from "@/lib/store"

export function MetricStrip() {
  const { results, mode, processingTime, wordCount } = useAppStore()
  if (!results) return null

  const keyPoints =
    mode === "study"
      ? results.key_facts?.length || 0
      : mode === "work"
        ? results.key_points?.length || 0
        : results.key_takeaways?.length || 0

  const stats = [
    { label: "Processing Time", value: processingTime ? `${(processingTime / 1000).toFixed(1)}s` : "0s" },
    { label: "Video Length", value: "Real-time" },
    { label: "Word Count", value: wordCount ? wordCount.toLocaleString() : "0" },
    { label: "Key Points", value: `${keyPoints}` },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/5">
      {stats.map((item) => (
        <div key={item.label} className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-xs text-white/40 mb-1">{item.label}</div>
          <div className="text-sm text-white/90">{item.value}</div>
        </div>
      ))}
    </div>
  )
}
