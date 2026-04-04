"use client"

import { useEffect, useMemo, useState } from "react"
import { Navbar } from "@/components/layout/Navbar"
import { useAppStore } from "@/lib/store"
import { smartWatchAnalytics, smartWatchDashboard, smartWatchHistory, getLibrary } from "@/lib/api"
import { SmartWatchDashboardResponse, SmartWatchHistoryItem, UnifiedLibraryItem, LibraryContentType } from "@/lib/types"
import Link from "next/link"

function formatMs(ms: number) {
  if (!ms) return "0s"
  return `${(ms / 1000).toFixed(1)}s`
}

type SortKey = "newest" | "oldest" | "confidence"
type VerdictFilter = "all" | "watch" | "skim" | "skip"
type ModeFilter = "all" | "study" | "work" | "quick"
type DateFilter = "all" | "today" | "week" | "month"
type ContentTypeFilter = "all" | LibraryContentType

const selectStyle = { colorScheme: "light" } as const
const selectClassName =
  "bg-white/80 border border-[#ddd4f6] rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-primary/35 focus:bg-white transition-colors"
const optionClassName = "bg-white text-slate-800"

function inferMode(item: SmartWatchHistoryItem): "study" | "work" | "quick" {
  const verdict = String(item.verdict || "").toLowerCase()
  if (verdict === "watch" || verdict === "skim" || verdict === "skip") return "quick"
  const question = String(item.user_question || "").toLowerCase()
  if (question.includes("work") || question.includes("team")) return "work"
  return "study"
}

function isInDateRange(value: string | undefined, filter: DateFilter): boolean {
  if (filter === "all") return true
  if (!value) return false
  const ts = new Date(value).getTime()
  if (Number.isNaN(ts)) return false
  const now = Date.now()
  const diff = now - ts
  if (filter === "today") return diff <= 24 * 60 * 60 * 1000
  if (filter === "week") return diff <= 7 * 24 * 60 * 60 * 1000
  return diff <= 30 * 24 * 60 * 60 * 1000
}

export default function LibraryPage() {
  const { sessionId, userId } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [query, setQuery] = useState("")
  const [verdictFilter, setVerdictFilter] = useState<VerdictFilter>("all")
  const [modeFilter, setModeFilter] = useState<ModeFilter>("all")
  const [dateFilter, setDateFilter] = useState<DateFilter>("all")
  const [sortBy, setSortBy] = useState<SortKey>("newest")
  const [visibleCount, setVisibleCount] = useState(12)
  const [selected, setSelected] = useState<SmartWatchHistoryItem | null>(null)
  const [items, setItems] = useState<SmartWatchHistoryItem[]>([])
  const [metrics, setMetrics] = useState<SmartWatchDashboardResponse | null>(null)

  useEffect(() => {
    if (!sessionId) return
    let mounted = true
    const run = async () => {
      setLoading(true)
      setError("")
      try {
        const [history, dashboard] = await Promise.all([
          smartWatchHistory(sessionId, userId, 100),
          smartWatchDashboard(sessionId, userId),
        ])
        if (!mounted) return
        setItems(history.items || [])
        setMetrics(dashboard)
      } catch {
        if (!mounted) return
        setError("Couldn’t load your library right now.")
      } finally {
        if (mounted) setLoading(false)
      }
    }
    run()
    return () => {
      mounted = false
    }
  }, [sessionId, userId])

  const filteredSorted = useMemo(() => {
    const q = query.trim().toLowerCase()
    const out = items.filter((item) => {
      if (verdictFilter !== "all" && String(item.verdict || "").toLowerCase() !== verdictFilter) return false
      if (modeFilter !== "all" && inferMode(item) !== modeFilter) return false
      if (!isInDateRange(item.created_at, dateFilter)) return false
      if (!q) return true
      const text = `${item.user_question} ${item.video_title || ""} ${item.reason || ""}`.toLowerCase()
      return text.includes(q)
    })

    out.sort((a, b) => {
      if (sortBy === "confidence") {
        const ac = typeof a.confidence === "number" ? a.confidence : -1
        const bc = typeof b.confidence === "number" ? b.confidence : -1
        return bc - ac
      }
      const at = a.created_at ? new Date(a.created_at).getTime() : 0
      const bt = b.created_at ? new Date(b.created_at).getTime() : 0
      return sortBy === "newest" ? bt - at : at - bt
    })
    return out
  }, [items, query, verdictFilter, modeFilter, dateFilter, sortBy])

  useEffect(() => {
    setVisibleCount(12)
  }, [query, verdictFilter, modeFilter, dateFilter, sortBy])

  const visibleItems = useMemo(
    () => filteredSorted.slice(0, visibleCount),
    [filteredSorted, visibleCount]
  )

  const hasMore = visibleCount < filteredSorted.length

  return (
    <div className="min-h-screen text-slate-900 relative overflow-hidden">
      <Navbar />
      <main className="pt-20 max-w-6xl mx-auto px-8 pb-12 space-y-6 relative z-[1]">
        <div className="surface-premium rounded-2xl p-6">
          <div className="text-xs uppercase tracking-[0.14em] text-slate-500 mb-2">Library</div>
          <h1 className="text-2xl font-semibold tracking-tight">Your Learning & Decision Archive</h1>
          <p className="text-sm text-slate-600 mt-2">
            Review what you asked, what the system recommended, and where answers were found.
          </p>
          <div className="mt-4 flex items-center gap-2">
            <Link
              href="/app"
              className="px-3 py-1.5 rounded-lg text-xs bg-white/80 hover:bg-[#f6f2ff] text-slate-700 border border-[#ddd4f6]"
            >
              Back to App
            </Link>
          </div>
        </div>

        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            <div className="surface-premium rounded-xl p-4">
              <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Total analyses</div>
              <div className="text-2xl mt-1">{metrics.total_analyses}</div>
            </div>
            <div className="surface-premium rounded-xl p-4">
              <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Verdicts</div>
              <div className="text-sm mt-2 text-slate-700">
                Watch {metrics.watch_count} · Skim {metrics.skim_count} · Skip {metrics.skip_count}
              </div>
            </div>
            <div className="surface-premium rounded-xl p-4">
              <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Avg confidence</div>
              <div className="text-2xl mt-1">{Math.round((metrics.avg_confidence || 0) * 100)}%</div>
            </div>
            <div className="surface-premium rounded-xl p-4">
              <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Timestamp utility</div>
              <div className="text-sm mt-2 text-slate-700">
                {metrics.timestamp_clicks} clicks / {metrics.timestamps_generated} generated
              </div>
            </div>
            <div className="surface-premium rounded-xl p-4 md:col-span-2">
              <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Speed profile</div>
              <div className="text-sm mt-2 text-slate-700">
                Quick-check {formatMs(metrics.avg_stage1_ms)} · Deep-analysis {formatMs(metrics.avg_stage2_ms)}
              </div>
            </div>
            <div className="surface-premium rounded-xl p-4 md:col-span-2">
              <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Estimated time saved</div>
              <div className="text-2xl mt-1">{(metrics.estimated_time_saved_minutes || 0).toFixed(1)} min</div>
              <div className="text-xs text-slate-500 mt-1">Based on skip + skim decisions and cached video durations</div>
            </div>
          </div>
        )}

        <div className="surface-premium rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-slate-800">Analyses</div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search question, reason, title..."
              className="w-full md:w-auto md:min-w-[280px] bg-white/80 border border-[#ddd4f6] rounded-lg px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#d8d0f4]"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value as VerdictFilter)}
              className={selectClassName}
              style={selectStyle}
            >
              <option value="all" className={optionClassName}>All verdicts</option>
              <option value="watch" className={optionClassName}>Watch</option>
              <option value="skim" className={optionClassName}>Skim</option>
              <option value="skip" className={optionClassName}>Skip</option>
            </select>
            <select
              value={modeFilter}
              onChange={(e) => setModeFilter(e.target.value as ModeFilter)}
              className={selectClassName}
              style={selectStyle}
            >
              <option value="all" className={optionClassName}>All modes</option>
              <option value="quick" className={optionClassName}>Quick</option>
              <option value="study" className={optionClassName}>Study</option>
              <option value="work" className={optionClassName}>Work</option>
            </select>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value as DateFilter)}
              className={selectClassName}
              style={selectStyle}
            >
              <option value="all" className={optionClassName}>Any time</option>
              <option value="today" className={optionClassName}>Today</option>
              <option value="week" className={optionClassName}>Last 7 days</option>
              <option value="month" className={optionClassName}>Last 30 days</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className={selectClassName}
              style={selectStyle}
            >
              <option value="newest" className={optionClassName}>Newest first</option>
              <option value="oldest" className={optionClassName}>Oldest first</option>
              <option value="confidence" className={optionClassName}>Highest confidence</option>
            </select>
          </div>

          {loading && <div className="text-sm text-slate-500">Loading library...</div>}
          {error && <div className="text-sm text-red-300">{error}</div>}
          {!loading && !filteredSorted.length && <div className="text-sm text-slate-500">No matching items yet.</div>}

          <div className="space-y-2 max-h-[540px] overflow-y-auto pr-1">
            {visibleItems.map((item, i) => (
              <button
                type="button"
                key={`${item.id || i}`}
                onClick={() => setSelected(item)}
                className="w-full text-left rounded-xl border border-[#ddd4f6] bg-white/82 p-4 space-y-2 hover:bg-[#f4f0ff] transition-colors"
              >
                <div className="text-sm text-slate-900">{item.user_question}</div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <span className="px-2 py-0.5 rounded-full border border-[#d8d0f4] bg-white/80">
                    {(item.verdict || "unknown").toString().toUpperCase()}
                  </span>
                  {typeof item.confidence === "number" && (
                    <span>{Math.round(item.confidence * 100)}% confidence</span>
                  )}
                  {item.created_at && <span>· {new Date(item.created_at).toLocaleString()}</span>}
                </div>
                {item.reason && <div className="text-sm text-slate-700">{item.reason}</div>}
                {item.relevant_moments && item.relevant_moments.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {item.relevant_moments.slice(0, 5).map((m, idx) => (
                      <a
                        key={`${m.timestamp_seconds}-${idx}`}
                        href={m.youtube_url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => {
                          e.stopPropagation()
                          if (sessionId) {
                            void smartWatchAnalytics(
                              sessionId,
                              "smart_watch_timestamp_clicked",
                              userId || null,
                              { video_id: item.video_id, timestamp_seconds: m.timestamp_seconds, source: "library_list" }
                            )
                          }
                        }}
                        className="text-xs px-2.5 py-1 rounded-full border border-[#d8d0f4] bg-white/80 hover:bg-[#f6f2ff] text-slate-700"
                        title={`${m.quote} — ${m.relevance}`}
                      >
                        ▶ {m.timestamp_display}
                      </a>
                    ))}
                  </div>
                )}
              </button>
            ))}
          </div>

          {hasMore && (
            <button
              type="button"
              onClick={() => setVisibleCount((c) => c + 12)}
              className="w-full rounded-lg border border-[#d8d0f4] bg-white/80 py-2 text-sm text-slate-800 hover:bg-[#f6f2ff] transition-colors"
            >
              Load 12 more
            </button>
          )}
        </div>
      </main>

      {selected && (
        <div className="fixed inset-0 z-50 bg-black/55 backdrop-blur-sm p-4 md:p-8">
          <div className="max-w-3xl mx-auto mt-8 surface-premium rounded-2xl border border-[#ddd4f6] p-5 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-[0.12em] text-slate-500">Run details</div>
                <h3 className="text-lg text-slate-900 mt-1">{selected.user_question}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="rounded-lg border border-[#d8d0f4] bg-white/80 px-2.5 py-1 text-xs text-slate-700 hover:bg-[#f6f2ff]"
              >
                Close
              </button>
            </div>

            <div className="flex flex-wrap gap-2 text-xs text-slate-700">
              <span className="px-2 py-0.5 rounded-full border border-[#d8d0f4] bg-white/80">
                {(selected.verdict || "unknown").toString().toUpperCase()}
              </span>
              <span className="px-2 py-0.5 rounded-full border border-[#d8d0f4] bg-white/80">
                Mode {inferMode(selected).toUpperCase()}
              </span>
              {typeof selected.confidence === "number" && (
                <span>{Math.round(selected.confidence * 100)}% confidence</span>
              )}
              {selected.created_at && <span>· {new Date(selected.created_at).toLocaleString()}</span>}
            </div>

            {selected.reason && <p className="text-sm text-slate-700">{selected.reason}</p>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="rounded-lg border border-[#ddd4f6] bg-white/82 p-3">
                Video ID: <span className="text-slate-800">{selected.video_id}</span>
              </div>
              <div className="rounded-lg border border-[#ddd4f6] bg-white/82 p-3">
                Est. range: <span className="text-slate-800">{selected.estimated_timestamp_range || "—"}</span>
              </div>
              <div className="rounded-lg border border-[#ddd4f6] bg-white/82 p-3">
                Stage 1: <span className="text-slate-800">{formatMs(selected.stage1_ms || 0)}</span>
              </div>
              <div className="rounded-lg border border-[#ddd4f6] bg-white/82 p-3">
                Stage 2: <span className="text-slate-800">{formatMs(selected.stage2_ms || 0)}</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm text-slate-800">Relevant moments</div>
              {selected.relevant_moments && selected.relevant_moments.length > 0 ? (
                <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
                  {selected.relevant_moments.map((m, idx) => (
                    <a
                      key={`${m.timestamp_seconds}-${idx}`}
                      href={m.youtube_url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={() => {
                        if (sessionId) {
                          void smartWatchAnalytics(
                            sessionId,
                            "smart_watch_timestamp_clicked",
                            userId || null,
                            { video_id: selected.video_id, timestamp_seconds: m.timestamp_seconds, source: "library_detail" }
                          )
                        }
                      }}
                      className="block rounded-lg border border-[#ddd4f6] bg-white/82 p-3 hover:bg-[#f4f0ff] transition-colors"
                    >
                      <div className="text-xs text-slate-700 mb-1">▶ {m.timestamp_display}</div>
                      <div className="text-sm text-slate-900">{m.quote || "Moment reference"}</div>
                      <div className="text-xs text-slate-600 mt-1">{m.relevance}</div>
                    </a>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-slate-500">No extracted moments for this run.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


