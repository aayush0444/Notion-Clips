"use client"
import { useAppStore } from '@/lib/store'

export function MetricStrip() {
  const { results, mode } = useAppStore()
  if (!results) return null

  const stats = [
    { label: "Processing time", value: "4.2s" },
    { label: "Video length", value: "14m 20s" },
    { label: "Word count", value: "2,105" },
    { label: "Key points", value: mode === 'study' ? results.key_facts?.length : (mode === 'work' ? results.key_points?.length : results.key_takeaways?.length) }
  ]

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
      {stats.map((s, i) => (
        <div key={i} className="flex-1 min-w-[120px] bg-white/[0.02] border border-border flex flex-col items-center rounded-2xl p-4 text-center">
          <p className="text-xs text-muted mb-1 font-medium">{s.label}</p>
          <p className="text-2xl font-display text-white font-bold">{s.value || 0}</p>
        </div>
      ))}
    </div>
  )
}
