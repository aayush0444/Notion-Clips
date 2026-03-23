"use client"
import { useAppStore } from '@/lib/store'

export function MetricStrip() {
  const { results, mode, processingTime, wordCount } = useAppStore()
  if (!results) return null

  const stats = [
    { label: "Processing time", value: processingTime ? `${(processingTime / 1000).toFixed(1)}s` : "0s" },
    { label: "Video length", value: "Real-time" },
    { label: "Word count", value: wordCount ? wordCount.toLocaleString() : "0" },
    { label: "Key points", value: mode === 'study' ? results.key_facts?.length : (mode === 'work' ? results.key_points?.length : results.key_takeaways?.length) }
  ]

  return (
    <div className="w-full">
      <div className="grid grid-cols-2 sm:grid-cols-4 items-stretch divide-x divide-white/10 border border-white/10 rounded-xl bg-white/[0.02] overflow-hidden">
        {stats.map((s, i) => (
          <div key={i} className="px-3 py-3 text-center">
            <p className="text-2xl font-display font-bold bg-gradient-to-r from-[#60A5FA] to-[#A78BFA] bg-clip-text text-transparent">{s.value || 0}</p>
            <p className="text-xs text-muted mt-1">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
