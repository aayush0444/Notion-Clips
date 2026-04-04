"use client"

import { useEffect, useMemo, useState } from "react"
import { Navbar } from "@/components/layout/Navbar"
import { useAppStore } from "@/lib/store"
import { getLibrary } from "@/lib/api"
import { UnifiedLibraryItem, LibraryContentType } from "@/lib/types"
import Link from "next/link"

type ContentTypeFilter = "all" | LibraryContentType
type DateFilter = "all" | "today" | "week" | "month"
type SortKey = "newest" | "oldest"

const selectStyle = { colorScheme: "light" } as const
const selectClassName =
  "bg-white/80 border border-[#ddd4f6] rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-primary/35 focus:bg-white transition-colors"
const optionClassName = "bg-white text-slate-800"

function getContentTypeInfo(type: LibraryContentType) {
  const typeMap = {
    youtube_study: { label: "Study", emoji: "📚", color: "bg-blue-50 border-blue-200 text-blue-700" },
    youtube_work: { label: "Work", emoji: "💼", color: "bg-purple-50 border-purple-200 text-purple-700" },
    youtube_quick: { label: "Quick", emoji: "⚡", color: "bg-yellow-50 border-yellow-200 text-yellow-700" },
    smart_watch: { label: "Smart Watch", emoji: "👀", color: "bg-green-50 border-green-200 text-green-700" },
    study_session: { label: "Study Session", emoji: "🎓", color: "bg-pink-50 border-pink-200 text-pink-700" },
  }
  return typeMap[type] || { label: type, emoji: "📄", color: "bg-gray-50 border-gray-200 text-gray-700" }
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

function formatDate(dateStr: string) {
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return dateStr
  }
}

function LibraryItemCard({ item, onClick }: { item: UnifiedLibraryItem; onClick: () => void }) {
  const typeInfo = getContentTypeInfo(item.content_type)
  
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left rounded-xl border border-[#ddd4f6] bg-white/90 hover:bg-[#f8f6ff] p-4 space-y-3 transition-all hover:shadow-md group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-slate-900 truncate group-hover:text-primary transition-colors">
            {item.title}
          </h3>
          {item.summary && (
            <p className="text-xs text-slate-600 mt-1 line-clamp-2">{item.summary}</p>
          )}
        </div>
        <span className={`px-2 py-1 rounded-lg text-[10px] font-medium border whitespace-nowrap ${typeInfo.color}`}>
          {typeInfo.emoji} {typeInfo.label}
        </span>
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-500">
        <span>{formatDate(item.created_at)}</span>
        {item.notion_page_id && (
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">
            📄 Notion
          </span>
        )}
        {item.source_url && (
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">
            🔗 Source
          </span>
        )}
      </div>
    </button>
  )
}

function DetailModal({ item, onClose }: { item: UnifiedLibraryItem; onClose: () => void }) {
  const typeInfo = getContentTypeInfo(item.content_type)
  const data = item.content_data as any

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="surface-premium rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-1 rounded-lg text-xs font-medium border ${typeInfo.color}`}>
                {typeInfo.emoji} {typeInfo.label}
              </span>
              <span className="text-xs text-slate-500">{formatDate(item.created_at)}</span>
            </div>
            <h2 className="text-xl font-semibold text-slate-900">{item.title}</h2>
            {item.summary && (
              <p className="text-sm text-slate-600 mt-2">{item.summary}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-xs bg-white/80 hover:bg-slate-100 text-slate-700 border border-[#ddd4f6]"
          >
            Close
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          {item.notion_page_id && (
            <a
              href={`https://notion.so/${item.notion_page_id.replace(/-/g, '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg text-xs bg-[#f6f2ff] hover:bg-[#eee6ff] text-primary border border-primary/20"
            >
              📄 Open in Notion
            </a>
          )}
          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg text-xs bg-white/80 hover:bg-slate-100 text-slate-700 border border-[#ddd4f6]"
            >
              🔗 View Source
            </a>
          )}
        </div>

        <div className="border-t border-[#ddd4f6] pt-4 space-y-4">
          {/* YouTube Study Content */}
          {item.content_type === 'youtube_study' && (
            <>
              {data.core_concept && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Core Concept</h3>
                  <p className="text-sm text-slate-800 bg-blue-50 p-3 rounded-lg">{data.core_concept}</p>
                </div>
              )}
              {data.key_facts && data.key_facts.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Key Facts</h3>
                  <ul className="space-y-1.5">
                    {data.key_facts.slice(0, 5).map((fact: string, i: number) => (
                      <li key={i} className="text-sm text-slate-700 flex gap-2">
                        <span className="text-blue-500">•</span>
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {data.formula_sheet && data.formula_sheet.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Formulas</h3>
                  <div className="bg-slate-50 p-3 rounded-lg font-mono text-xs space-y-1">
                    {data.formula_sheet.slice(0, 3).map((formula: string, i: number) => (
                      <div key={i}>{formula}</div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* YouTube Work Content */}
          {item.content_type === 'youtube_work' && (
            <>
              {data.one_liner && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Summary</h3>
                  <p className="text-sm text-slate-800 bg-purple-50 p-3 rounded-lg">{data.one_liner}</p>
                </div>
              )}
              {data.recommendation && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Recommendation</h3>
                  <p className="text-sm text-slate-800 bg-yellow-50 p-3 rounded-lg">{data.recommendation}</p>
                </div>
              )}
              {data.key_points && data.key_points.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Key Points</h3>
                  <ul className="space-y-1.5">
                    {data.key_points.slice(0, 5).map((point: string, i: number) => (
                      <li key={i} className="text-sm text-slate-700 flex gap-2">
                        <span className="text-purple-500">•</span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {data.tools_mentioned && data.tools_mentioned.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Tools Mentioned</h3>
                  <div className="flex flex-wrap gap-2">
                    {data.tools_mentioned.map((tool: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* YouTube Quick Content */}
          {item.content_type === 'youtube_quick' && (
            <>
              {data.summary && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Summary</h3>
                  <p className="text-sm text-slate-800">{data.summary}</p>
                </div>
              )}
              {data.key_takeaways && data.key_takeaways.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Key Takeaways</h3>
                  <ul className="space-y-1.5">
                    {data.key_takeaways.map((takeaway: string, i: number) => (
                      <li key={i} className="text-sm text-slate-700 flex gap-2">
                        <span className="text-yellow-500">•</span>
                        <span>{takeaway}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {/* Smart Watch Content */}
          {item.content_type === 'smart_watch' && (
            <>
              {data.user_question && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Question</h3>
                  <p className="text-sm text-slate-800 italic">{data.user_question}</p>
                </div>
              )}
              {data.verdict && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Verdict</h3>
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-lg text-sm font-medium uppercase">
                      {data.verdict}
                    </span>
                    {data.confidence && (
                      <span className="text-xs text-slate-600">
                        {Math.round(data.confidence * 100)}% confidence
                      </span>
                    )}
                  </div>
                </div>
              )}
              {data.reason && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Reason</h3>
                  <p className="text-sm text-slate-700">{data.reason}</p>
                </div>
              )}
              {data.estimated_timestamp_range && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Relevant Timeframe</h3>
                  <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-sm">
                    {data.estimated_timestamp_range}
                  </span>
                </div>
              )}
            </>
          )}

          {/* Study Session Content */}
          {item.content_type === 'study_session' && (
            <>
              {data.learning_goal && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Learning Goal</h3>
                  <p className="text-sm text-slate-800 bg-pink-50 p-3 rounded-lg">{data.learning_goal}</p>
                </div>
              )}
              {data.student_level && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Level</h3>
                  <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs capitalize">
                    {data.student_level.replace('_', ' ')}
                  </span>
                </div>
              )}
              {data.concepts && data.concepts.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Concepts Covered</h3>
                  <div className="space-y-2">
                    {data.concepts.slice(0, 3).map((concept: any, i: number) => (
                      <div key={i} className="bg-slate-50 p-2 rounded text-xs">
                        <div className="font-medium text-slate-800">{concept.concept_name}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {data.sources && data.sources.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-2">Sources</h3>
                  <div className="space-y-1">
                    {data.sources.map((source: any, i: number) => (
                      <div key={i} className="text-xs text-slate-600">
                        {source.type === 'youtube' && '📺'}
                        {source.type === 'pdf' && '📄'}
                        {source.type === 'article' && '🌐'}
                        {' '}{source.title}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function LibraryPage() {
  const { sessionId, userId } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [query, setQuery] = useState("")
  const [contentTypeFilter, setContentTypeFilter] = useState<ContentTypeFilter>("all")
  const [dateFilter, setDateFilter] = useState<DateFilter>("all")
  const [sortBy, setSortBy] = useState<SortKey>("newest")
  const [items, setItems] = useState<UnifiedLibraryItem[]>([])
  const [selected, setSelected] = useState<UnifiedLibraryItem | null>(null)

  useEffect(() => {
    if (!sessionId) return
    let mounted = true
    const run = async () => {
      setLoading(true)
      setError("")
      try {
        const library = await getLibrary(
          sessionId, 
          userId, 
          contentTypeFilter === 'all' ? undefined : contentTypeFilter, 
          100
        )
        if (!mounted) return
        setItems(library.items || [])
      } catch (err: any) {
        if (!mounted) return
        setError(err?.message || "Couldn't load your library right now.")
      } finally {
        if (mounted) setLoading(false)
      }
    }
    run()
    return () => {
      mounted = false
    }
  }, [sessionId, userId, contentTypeFilter])

  const filteredSorted = useMemo(() => {
    const q = query.trim().toLowerCase()
    let filtered = items.filter((item) => {
      if (!isInDateRange(item.created_at, dateFilter)) return false
      if (!q) return true
      const searchText = `${item.title} ${item.summary || ""}`.toLowerCase()
      return searchText.includes(q)
    })

    filtered.sort((a, b) => {
      const at = new Date(a.created_at).getTime()
      const bt = new Date(b.created_at).getTime()
      return sortBy === "newest" ? bt - at : at - bt
    })

    return filtered
  }, [items, query, dateFilter, sortBy])

  const stats = useMemo(() => {
    const total = items.length
    const byType: Record<string, number> = {}
    items.forEach(item => {
      byType[item.content_type] = (byType[item.content_type] || 0) + 1
    })
    return { total, byType }
  }, [items])

  return (
    <div className="min-h-screen text-slate-900 relative overflow-hidden">
      <Navbar />
      <main className="pt-20 max-w-6xl mx-auto px-8 pb-12 space-y-6 relative z-[1]">
        {/* Header */}
        <div className="surface-premium rounded-2xl p-6">
          <div className="text-xs uppercase tracking-[0.14em] text-slate-500 mb-2">Library</div>
          <h1 className="text-2xl font-semibold tracking-tight">Your Personal Knowledge Space</h1>
          <p className="text-sm text-slate-600 mt-2">
            All your processed content from YouTube, Study Sessions, and Smart Watch in one unified library.
          </p>
          <div className="mt-4 flex items-center gap-2">
            <Link
              href="/app"
              className="px-3 py-1.5 rounded-lg text-xs bg-white/80 hover:bg-[#f6f2ff] text-slate-700 border border-[#ddd4f6]"
            >
              ← Back to App
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="surface-premium rounded-xl p-3">
            <div className="text-xs text-slate-500 uppercase tracking-[0.12em]">Total</div>
            <div className="text-xl mt-1 font-semibold">{stats.total}</div>
          </div>
          <div className="surface-premium rounded-xl p-3">
            <div className="text-xs text-slate-500 mb-1">📚 Study</div>
            <div className="text-lg font-medium">{stats.byType.youtube_study || 0}</div>
          </div>
          <div className="surface-premium rounded-xl p-3">
            <div className="text-xs text-slate-500 mb-1">💼 Work</div>
            <div className="text-lg font-medium">{stats.byType.youtube_work || 0}</div>
          </div>
          <div className="surface-premium rounded-xl p-3">
            <div className="text-xs text-slate-500 mb-1">⚡ Quick</div>
            <div className="text-lg font-medium">{stats.byType.youtube_quick || 0}</div>
          </div>
          <div className="surface-premium rounded-xl p-3">
            <div className="text-xs text-slate-500 mb-1">👀 Smart Watch</div>
            <div className="text-lg font-medium">{stats.byType.smart_watch || 0}</div>
          </div>
          <div className="surface-premium rounded-xl p-3">
            <div className="text-xs text-slate-500 mb-1">🎓 Sessions</div>
            <div className="text-lg font-medium">{stats.byType.study_session || 0}</div>
          </div>
        </div>

        {/* Filters */}
        <div className="surface-premium rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm font-medium text-slate-800">
              {filteredSorted.length} {filteredSorted.length === 1 ? 'item' : 'items'}
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search title, summary..."
              className="w-full md:w-auto md:min-w-[280px] bg-white/80 border border-[#ddd4f6] rounded-lg px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#d8d0f4]"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <select
              value={contentTypeFilter}
              onChange={(e) => setContentTypeFilter(e.target.value as ContentTypeFilter)}
              className={selectClassName}
              style={selectStyle}
            >
              <option value="all" className={optionClassName}>All Types</option>
              <option value="youtube_study" className={optionClassName}>📚 Study</option>
              <option value="youtube_work" className={optionClassName}>💼 Work</option>
              <option value="youtube_quick" className={optionClassName}>⚡ Quick</option>
              <option value="smart_watch" className={optionClassName}>👀 Smart Watch</option>
              <option value="study_session" className={optionClassName}>🎓 Study Session</option>
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
            </select>
          </div>

          {/* Content */}
          {loading && (
            <div className="text-center py-12 text-sm text-slate-500">
              Loading your library...
            </div>
          )}
          
          {error && (
            <div className="text-center py-12">
              <div className="text-sm text-red-600 bg-red-50 inline-block px-4 py-2 rounded-lg">
                {error}
              </div>
            </div>
          )}

          {!loading && !error && filteredSorted.length === 0 && (
            <div className="text-center py-12 space-y-2">
              <div className="text-4xl">📚</div>
              <div className="text-sm text-slate-600">
                {items.length === 0 
                  ? "Your library is empty. Start processing videos to build your knowledge base!"
                  : "No items match your filters."}
              </div>
            </div>
          )}

          {!loading && !error && filteredSorted.length > 0 && (
            <div className="grid gap-3 md:grid-cols-2">
              {filteredSorted.map((item) => (
                <LibraryItemCard 
                  key={item.id} 
                  item={item} 
                  onClick={() => setSelected(item)} 
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {selected && <DetailModal item={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
