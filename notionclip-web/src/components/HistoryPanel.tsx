"use client"

import { useEffect, useMemo, useState } from "react"
import { smartWatchHistory } from "@/lib/api"
import { SmartWatchHistoryItem } from "@/lib/types"
import { useAppStore } from "@/lib/store"

function timeAgo(iso?: string) {
  if (!iso) return "just now"
  const d = new Date(iso).getTime()
  if (!Number.isFinite(d)) return "recently"
  const diff = Math.max(0, Date.now() - d)
  const m = Math.floor(diff / 60000)
  if (m < 1) return "just now"
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const days = Math.floor(h / 24)
  return `${days}d ago`
}

export function HistoryPanel() {
  const { sessionId, userId } = useAppStore()
  const [items, setItems] = useState<SmartWatchHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [query, setQuery] = useState("")

  useEffect(() => {
    if (!sessionId) return
    let mounted = true
    const run = async () => {
      setLoading(true)
      setError("")
      try {
        const res = await smartWatchHistory(sessionId, userId, 24)
        if (mounted) setItems(res.items || [])
      } catch {
        if (mounted) setError("Couldn’t load history right now.")
      } finally {
        if (mounted) setLoading(false)
      }
    }
    run()
    return () => {
      mounted = false
    }
  }, [sessionId, userId])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((item) => {
      const text = `${item.user_question} ${item.reason || ""} ${item.video_title || ""}`.toLowerCase()
      return text.includes(q)
    })
  }, [items, query])

  return (
    <div className="surface-premium rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-white/45 uppercase tracking-[0.14em]">History</div>
          <div className="text-sm text-white/80">Recent analyses and verdicts</div>
        </div>
        <div className="text-xs text-white/40">{items.length} items</div>
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by question, reason, or title..."
        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/85 placeholder:text-white/35 focus:outline-none focus:border-white/20"
      />

      {loading && <div className="text-sm text-white/50">Loading history...</div>}
      {error && <div className="text-sm text-red-300">{error}</div>}

      {!loading && !filtered.length && (
        <div className="text-sm text-white/45">No saved analyses yet. Run Smart Watch to start building your library.</div>
      )}

      <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
        {filtered.map((item, i) => (
          <div key={`${item.id || item.created_at || i}`} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm text-white/85 line-clamp-1">{item.user_question}</div>
              <div className="text-[11px] text-white/45 whitespace-nowrap">{timeAgo(item.created_at)}</div>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span
                className={`px-2 py-0.5 rounded-full border ${
                  String(item.verdict || "").toLowerCase() === "watch"
                    ? "border-green-500/40 text-green-300 bg-green-500/10"
                    : String(item.verdict || "").toLowerCase() === "skim"
                      ? "border-yellow-500/40 text-yellow-300 bg-yellow-500/10"
                      : "border-red-500/35 text-red-300 bg-red-500/10"
                }`}
              >
                {(item.verdict || "unknown").toString().toUpperCase()}
              </span>
              {typeof item.confidence === "number" && (
                <span className="text-white/55">{Math.round(item.confidence * 100)}% confidence</span>
              )}
              {item.stage1_ms ? <span className="text-white/45">· {(item.stage1_ms / 1000).toFixed(1)}s</span> : null}
            </div>

            {item.reason && <div className="text-xs text-white/70 line-clamp-2">{item.reason}</div>}

            {item.relevant_moments && item.relevant_moments.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {item.relevant_moments.slice(0, 4).map((m, idx) => (
                  <a
                    key={`${m.timestamp_seconds}-${idx}`}
                    href={m.youtube_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] px-2 py-1 rounded-full border border-white/20 bg-white/5 hover:bg-white/10 text-white/80"
                    title={m.quote}
                  >
                    ▶ {m.timestamp_display}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

