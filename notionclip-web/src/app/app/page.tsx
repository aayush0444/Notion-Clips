"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Navbar } from "@/components/layout/Navbar"
import { ContentSourceSelector } from "@/components/app/ContentSourceSelector"
import { ModeSelector } from "@/components/app/ModeSelector"
import { ProcessButton } from "@/components/app/ProcessButton"
import { MetricStrip } from "@/components/app/MetricStrip"
import { SmartWatch } from "@/components/SmartWatch"
import { SynthesisMode } from "@/components/app/SynthesisMode"
import { StudyModeView } from "@/components/app/results/StudyModeView"
import { WorkModeView } from "@/components/app/results/WorkModeView"
import { QuickModeView } from "@/components/app/results/QuickModeView"
import { QnASection } from "@/components/app/QnASection"
import { Button } from "@/components/ui/Button"
import { api } from "@/lib/api"
import { useAppStore } from "@/lib/store"

const loadingMessagesByStage = {
  transcript: "Reading source context...",
  extract: "Crafting your mode-specific insights...",
  finalizing: "Polishing the final output..."
} as const

type TimestampNotePayload = {
  label: string
  seconds: number
  title: string
  note: string
}

function parseTimestampToSeconds(value: string): number | null {
  const parts = value.split(":").map((part) => Number(part))
  if (parts.some((part) => Number.isNaN(part))) return null
  if (parts.length === 2) {
    const [minutes, seconds] = parts
    return minutes * 60 + seconds
  }
  if (parts.length === 3) {
    const [hours, minutes, seconds] = parts
    return hours * 3600 + minutes * 60 + seconds
  }
  return null
}

function secondsToLabel(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = safe % 60
  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
  }
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
}

function buildTimestampNotes(data: unknown, limit: number = 8): TimestampNotePayload[] {
  const stack: unknown[] = [data]
  const moments: TimestampNotePayload[] = []
  const seen = new Set<string>()
  const timestampRegex = /(\b\d{1,2}:\d{2}(?::\d{2})?\b)/g

  while (stack.length > 0 && moments.length < limit) {
    const node = stack.pop()
    if (!node) continue

    if (Array.isArray(node)) {
      for (const item of node) stack.push(item)
      continue
    }

    if (typeof node === "object") {
      const record = node as Record<string, unknown>
      const display = typeof record.timestamp_display === "string" ? record.timestamp_display : null
      const rawTimestamp =
        typeof record.timestamp === "string"
          ? record.timestamp
          : typeof record.time === "string"
          ? record.time
          : null
      const rawSeconds =
        typeof record.timestamp_seconds === "number"
          ? record.timestamp_seconds
          : typeof record.seconds === "number"
          ? record.seconds
          : null
      const resolvedSeconds = rawSeconds ?? (rawTimestamp ? parseTimestampToSeconds(rawTimestamp) : null)
      if (resolvedSeconds !== null) {
        const label = display || rawTimestamp || secondsToLabel(resolvedSeconds)
        const explicitTitle =
          typeof record.title === "string"
            ? record.title
            : typeof record.topic === "string"
            ? record.topic
            : typeof record.concept === "string"
            ? record.concept
            : typeof record.key_point === "string"
            ? record.key_point
            : typeof record.point === "string"
            ? record.point
            : null
        const explicitNote =
          typeof record.note === "string"
            ? record.note
            : typeof record.description === "string"
            ? record.description
            : typeof record.relevance === "string"
            ? record.relevance
            : typeof record.quote === "string"
            ? record.quote
            : null
        const title = (explicitTitle || `Moment at ${label}`).trim()
        const note = (explicitNote || title).trim()
        const key = `${resolvedSeconds}-${title}`
        if (!seen.has(key)) {
          seen.add(key)
          moments.push({ label, seconds: resolvedSeconds, title, note })
          if (moments.length >= limit) break
        }
      }
      for (const value of Object.values(record)) stack.push(value)
      continue
    }

    if (typeof node === "string") {
      timestampRegex.lastIndex = 0
      let match: RegExpExecArray | null
      while ((match = timestampRegex.exec(node)) !== null) {
        const label = match[1]
        const seconds = parseTimestampToSeconds(label)
        if (seconds === null) continue
        const cleaned = node.replace(label, "").replace(/^[\s\-:.,]+/, "").trim()
        const title = cleaned.length > 0 ? cleaned.split(/\s+/).slice(0, 10).join(" ") : `Moment at ${label}`
        const note = cleaned.length > 0 ? cleaned : `Key moment at ${label}`
        const key = `${seconds}-${title}`
        if (!seen.has(key)) {
          seen.add(key)
          moments.push({ label, seconds, title, note })
          if (moments.length >= limit) break
        }
      }
    }
  }

  return moments.sort((a, b) => a.seconds - b.seconds)
}

function LoadingPanel({ stage }: { stage: keyof typeof loadingMessagesByStage }) {
  const currentMessage = loadingMessagesByStage[stage]
  const widths = ["100%", "85%", "70%", "90%"]
  return (
    <div className="space-y-6" aria-live="polite">
      <div className="flex items-center space-x-3 text-base app-text-muted">
        <span className="h-2.5 w-2.5 rounded-full bg-primary animate-pulse" />
        <AnimatePresence mode="wait">
          <motion.div
            key={stage}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.3 }}
          >
            {currentMessage}
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="space-y-4">
        {widths.map((w, idx) => (
          <div key={idx} className="relative overflow-hidden rounded-md bg-[#F0EBF8]/80 h-7" style={{ width: w }}>
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-[#9B7FD4]/20 to-transparent"
              initial={{ x: "-100%" }}
              animate={{ x: "100%" }}
              transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
              style={{ width: "120%" }}
            />
            <div style={{ width: w }} className="h-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AppPage() {
  const { results, mode, url, setUrl, setVideoId, sourceType, setSourceType, setMode } = useAppStore()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'extract' | 'synthesis'>('extract')
  const [showAdvancedControls, setShowAdvancedControls] = useState(false)
  const [leftWidth, setLeftWidth] = useState(430)
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStage, setProcessingStage] = useState<keyof typeof loadingMessagesByStage>("transcript")
  const [guideIndex, setGuideIndex] = useState(0)
  const [isGuideHovered, setIsGuideHovered] = useState(false)
  const [isPushingNotion, setIsPushingNotion] = useState(false)
  const [pushFeedback, setPushFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const [notionPageId, setNotionPageId] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const wasProcessingRef = useRef(false)
  const minLeft = 340
  const maxLeft = 520
  const minRight = 620

  const extractYoutubeId = useCallback((value: string) => {
    const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/
    const match = value.match(regExp)
    return match && match[2].length === 11 ? match[2] : null
  }, [])

  const handleFastStartYoutubeChange = useCallback((value: string) => {
    setUrl(value)
    setVideoId(extractYoutubeId(value))
  }, [setUrl, setVideoId, extractYoutubeId])
  const guideSlides = [
    {
      eyebrow: "Study Mode",
      title: "Build a memory-friendly study map",
      useCase: "Lecture revision and exam prep",
      reasonLines: [
        "You watched the video. You remember nothing.",
        "YouTube hooks you with thumbnails. You click.",
        "45 minutes later - no notes, no structure, no answer.",
        "NotionClip fixes the part YouTube never will.",
      ],
    },
    {
      eyebrow: "NotionClip Workspace",
      title: "Build output-ready intelligence, not raw notes.",
      useCase: "Three modes for three intentions",
      reasonLines: [
        "Study -> Deep notes, formulas, self-test questions.",
        "Work -> Watch or Skip verdict, decisions, action items.",
        "Quick -> 60-second summary and highest-signal takeaways.",
        "Smart Watch -> Ask first, then decide watch/skim/skip.",
      ],
    },
    {
      eyebrow: "Product Habit Loop",
      title: "Why NotionClip beats transcript-dump tools",
      useCase: "Question-first extraction + cross-source synthesis",
      reasonLines: [
        "We do not dump transcripts or generic summaries.",
        "We ask why you are watching before extraction starts.",
        "2 videos + 1 PDF + 1 article -> one unified answer.",
        "Study Session teaches, tests, and corrects progressively.",
      ],
    },
    {
      eyebrow: "Your Knowledge Library",
      title: "Everything worth keeping, searchable in Notion",
      useCase: "Build a repeatable system: source -> mode -> process -> review -> save",
      reasonLines: [
        "Every question, answer, and verdict in one place.",
        "Not a note-taking app. A learning-intelligence layer.",
        "Between what you consume and what you actually know.",
        "WATCH LESS. KNOW MORE.",
      ],
    },
  ] as const

  const goPrevGuide = useCallback(() => {
    setGuideIndex((prev) => (prev === 0 ? guideSlides.length - 1 : prev - 1))
  }, [guideSlides.length])

  const goNextGuide = useCallback(() => {
    setGuideIndex((prev) => (prev + 1) % guideSlides.length)
  }, [guideSlides.length])

  useEffect(() => {
    if (results || isProcessing || isGuideHovered) return
    const timer = window.setInterval(() => {
      goNextGuide()
    }, 4800)
    return () => window.clearInterval(timer)
  }, [results, isProcessing, isGuideHovered, goNextGuide])

  useEffect(() => {
    if (results || isProcessing) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowLeft") goPrevGuide()
      if (event.key === "ArrowRight") goNextGuide()
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [results, isProcessing, goPrevGuide, goNextGuide])

  useEffect(() => {
    if (!isResizing) return
    const handleMove = (event: PointerEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const separatorWidth = 10
      const dynamicMaxLeft = Math.max(minLeft, Math.min(maxLeft, rect.width - minRight - separatorWidth))
      let nextWidth = event.clientX - rect.left
      nextWidth = Math.max(minLeft, Math.min(dynamicMaxLeft, nextWidth))
      setLeftWidth(nextWidth)
    }
    const handleUp = () => setIsResizing(false)
    window.addEventListener("pointermove", handleMove)
    window.addEventListener("pointerup", handleUp)
    document.body.style.userSelect = "none"
    document.body.style.cursor = "col-resize"
    return () => {
      window.removeEventListener("pointermove", handleMove)
      window.removeEventListener("pointerup", handleUp)
      document.body.style.userSelect = ""
      document.body.style.cursor = ""
    }
  }, [isResizing, minLeft, maxLeft, minRight])

  useEffect(() => {
    if (typeof window === "undefined") return
    let id = window.localStorage.getItem("notionclip_session_id")
    if (!id) {
      id = crypto.randomUUID()
      window.localStorage.setItem("notionclip_session_id", id)
    }
    setSessionId(id)
  }, [])

  useEffect(() => {
    if (!showAdvancedControls) {
      if (sourceType !== "youtube") setSourceType("youtube")
      if (mode !== "study") setMode("study")
    }
  }, [showAdvancedControls, sourceType, mode, setSourceType, setMode])

  useEffect(() => {
    if (results || sourceType !== "youtube" || mode !== "study") {
      setShowAdvancedControls(true)
    }
  }, [results, sourceType, mode])

  useEffect(() => {
    if (wasProcessingRef.current && !isProcessing && results && !isLeftCollapsed) {
      setIsLeftCollapsed(true)
    }
    wasProcessingRef.current = isProcessing
  }, [isProcessing, results, isLeftCollapsed])

  const handleProcessingChange = (state: boolean) => {
    if (state) setProcessingStage("transcript")
    setIsProcessing(state)
  }

  const handleToggleLeftPanel = () => {
    setIsLeftCollapsed((prev) => {
      if (prev) setLeftWidth((current) => Math.max(current, minLeft))
      return !prev
    })
  }

  const handlePushAiNotesToNotion = async () => {
    if (!results || !sessionId) return
    setPushFeedback(null)
    setIsPushingNotion(true)
    try {
      const response = await api.pushToNotion(mode, results, url || "", sessionId)
      const rowPageId = response.row_page_id || response.page_id
      if (rowPageId) setNotionPageId(rowPageId)

      const timestampNotes = buildTimestampNotes(results)
      const aiSummary =
        mode === "study"
          ? ((results as Record<string, unknown>).core_concept as string | undefined) || ""
          : mode === "work"
          ? ((results as Record<string, unknown>).one_liner as string | undefined) || ((results as Record<string, unknown>).recommendation as string | undefined) || ""
          : ((results as Record<string, unknown>).summary as string | undefined) || ((results as Record<string, unknown>).title as string | undefined) || ""

      await api.pushTimestampNotesToNotion({
        mode,
        source_url: url || "",
        session_id: sessionId,
        notion_page_id: rowPageId || notionPageId,
        ai_summary: aiSummary || null,
        video_title: ((results as Record<string, unknown>).title as string | undefined) || null,
        creator_name: ((results as Record<string, unknown>).creator as string | undefined) || ((results as Record<string, unknown>).creator_name as string | undefined) || null,
        notes: timestampNotes,
      })

      setPushFeedback({
        type: "success",
        message: "✓ AI Notes and Timestamp Notes saved to your NotionClip library."
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : "Push to Notion failed"
      setPushFeedback({ type: "error", message })
    } finally {
      setIsPushingNotion(false)
    }
  }

  useEffect(() => {
    if (!pushFeedback) return
    const timer = window.setTimeout(() => {
      setPushFeedback(null)
    }, 5000)
    return () => window.clearTimeout(timer)
  }, [pushFeedback])

  return (
    <div className="min-h-screen text-foreground relative overflow-hidden">
      <Navbar />
      <div className="pointer-events-none absolute inset-0 z-0">
        <div className="absolute -top-36 right-[-8%] h-[520px] w-[520px] rounded-full bg-[#DCCEF6]/45 blur-[90px]" />
        <div className="absolute top-[34%] left-[-10%] h-[420px] w-[420px] rounded-full bg-[#F1DDE8]/45 blur-[95px]" />
        <div className="absolute bottom-[-14%] right-[18%] h-[360px] w-[360px] rounded-full bg-[#DCEEE0]/40 blur-[90px]" />
      </div>
      <div className="relative z-[1] px-4 pb-8 pt-20 sm:px-6 lg:px-8">
        <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-6">
          <div ref={containerRef} className="group/split relative min-h-[calc(100vh-11rem)] xl:flex xl:gap-0">
        <aside
          style={isLeftCollapsed ? { width: 0 } : { width: `${leftWidth}px` }}
          className={`min-w-0 xl:sticky xl:top-24 xl:h-[calc(100vh-8rem)] xl:overscroll-contain ${
            isLeftCollapsed
              ? "hidden xl:block xl:min-w-0 xl:max-w-0 xl:overflow-hidden xl:border-0 xl:bg-transparent xl:p-0 xl:shadow-none"
              : "flex flex-col overflow-y-auto overflow-x-hidden rounded-2xl border border-[#E4D9F5] bg-white/82 p-6 shadow-[0_12px_36px_rgba(61,36,102,0.09)] xl:min-w-[340px] xl:max-w-[520px]"
          } ${isResizing ? "" : "xl:transition-[width] xl:duration-200 xl:ease-out"}`}
        >
          {!isLeftCollapsed && (
          <div className="flex-1 min-w-0 space-y-6">
            <div className="py-2.5">
              <div className="text-center text-sm uppercase tracking-[0.14em] app-text-muted">Workspace Controls</div>
            </div>

            {!showAdvancedControls && (
              <div className="min-w-0 overflow-hidden rounded-xl border border-[#E8E2F6] bg-white/90 p-4">
                <div className="mb-4">
                  <div className="text-xs uppercase tracking-[0.12em] text-[#8E7AAE]">Fast Start</div>
                  <p className="mt-2 text-[1.02rem] leading-relaxed text-[#4D3D66] sm:text-base">
                    Paste one YouTube lecture URL and generate exam-ready study notes in one click.
                  </p>
                </div>
                <div className="space-y-3">
                  <label className="block text-sm app-text-muted uppercase tracking-[0.12em]">YouTube URL</label>
                  <div className="tech-gradient-ring">
                    <input
                      type="text"
                      value={url}
                      onChange={(event) => handleFastStartYoutubeChange(event.target.value)}
                      placeholder="https://youtube.com/watch?v=..."
                      className="bg-card px-4 py-4 text-[1.02rem] text-foreground placeholder:text-muted"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-sm text-[#7A5BB5]">
                    <div className="rounded-md border border-[#E4D9F5] bg-[#F8F4FF] px-2 py-2">1. Paste</div>
                    <div className="rounded-md border border-[#E4D9F5] bg-[#F8F4FF] px-2 py-2">2. Process</div>
                    <div className="rounded-md border border-[#E4D9F5] bg-[#F8F4FF] px-2 py-2">3. Review</div>
                  </div>
                </div>
              </div>
            )}

            {showAdvancedControls && (
              <div className="min-w-0 overflow-hidden rounded-xl border border-[#E8E2F6] bg-white/90 p-4">
                <ContentSourceSelector />
              </div>
            )}

            {sourceType === "youtube" && (
              <div className="min-w-0 overflow-hidden rounded-xl border border-[#F1E3C8] bg-[#FFF9EE] p-4">
                <div className="mb-3">
                  <div className="text-xs uppercase tracking-[0.12em] text-[#9D7C3F]">Smart Watch</div>
                  <div className="mt-1.5 text-[1.02rem] leading-relaxed text-[#6A5A38] sm:text-base">
                    {url
                      ? "YouTube-only pre-check is ready. Toggle Smart Watch on to decide watch, skim, or skip."
                      : "Smart Watch works only with YouTube URLs. Paste a YouTube link, then toggle it on."}
                  </div>
                </div>
                <SmartWatch videoUrl={url} sessionId={sessionId} />
              </div>
            )}

            {showAdvancedControls && sourceType !== "study_session" && (
              <div className="min-w-0 overflow-hidden rounded-xl border border-[#E8E2F6] bg-white/90 p-4">
                <ModeSelector onViewModeChange={setViewMode} />
              </div>
            )}

            {sourceType !== "study_session" && (
              <div className="min-w-0 overflow-hidden rounded-xl border border-[#E8E2F6] bg-white/90 p-4">
                <ProcessButton onProcessingChange={handleProcessingChange} onStageChange={setProcessingStage} />
              </div>
            )}

            <div className="flex items-center justify-center">
              <button
                type="button"
                onClick={() => setShowAdvancedControls((prev) => !prev)}
                className="text-sm font-medium text-[#6F52A8] underline-offset-4 transition hover:text-[#5C4390] hover:underline"
              >
                {showAdvancedControls
                  ? "Use fast start"
                  : "Show advanced controls (PDF, Article, Study Session, Synthesis)"}
              </button>
            </div>

            {results && (
              <div className="min-w-0 overflow-hidden rounded-xl border border-[#E8E2F6] bg-white/90 p-4">
                <MetricStrip />
              </div>
            )}

          </div>
          )}
        </aside>
        <div className="relative hidden xl:flex w-[10px] shrink-0 items-start justify-center">
          {!isLeftCollapsed && (
            <div
              role="separator"
              aria-orientation="vertical"
              onPointerDown={(event) => {
                event.preventDefault()
                setIsResizing(true)
              }}
              className={`absolute inset-0 touch-none transition-colors ${isResizing ? "cursor-col-resize bg-[#E4D9F5]/55" : "cursor-col-resize bg-transparent hover:bg-[#E4D9F5]/28"}`}
            />
          )}
          <div className={`pointer-events-none absolute bottom-0 top-0 left-1/2 w-px -translate-x-1/2 transition-colors ${isResizing ? "bg-[#BDA4E2]" : "bg-[#E4D9F5]"}`} />
          <button
            type="button"
            onClick={handleToggleLeftPanel}
            aria-label={isLeftCollapsed ? "Expand left panel" : "Collapse left panel"}
            className={`absolute left-1/2 top-6 z-20 flex h-6 w-6 -translate-x-1/2 items-center justify-center rounded-full border border-[#D8C9EE] bg-white text-[#7A5BB5] shadow-sm transition-all hover:bg-[#F7F2FF] focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D8C9EE] ${
              isLeftCollapsed ? "opacity-100" : "opacity-0 group-hover/split:opacity-100"
            }`}
          >
            {isLeftCollapsed ? ">" : "<"}
          </button>
        </div>

        <section className="min-w-0 flex-1 rounded-2xl border border-[#E4D9F5] bg-white/76 p-6 shadow-[0_12px_36px_rgba(61,36,102,0.09)] sm:p-7 lg:p-9 xl:h-[calc(100vh-8rem)] xl:overflow-y-auto xl:overscroll-contain">
          <div className="w-full space-y-7">
            <div className="py-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-[0.14em] app-text-muted">Intelligence Canvas</p>
                  <p className="mt-2 text-[1.06rem] leading-relaxed text-[#4D3D66] sm:text-lg">
                    AI output, guidance, and teach-back will appear here.
                  </p>
                </div>
                {results && !isProcessing && viewMode === "extract" && sourceType !== "study_session" && (
                  <button
                    type="button"
                    onClick={handlePushAiNotesToNotion}
                    disabled={isPushingNotion || !sessionId}
                    className="rounded-lg border border-[#D6C7EF] bg-[#F7F1FF] px-4 py-2.5 text-sm font-semibold text-[#5E4496] transition hover:border-[#BFA8E4] hover:bg-[#EFE3FF] disabled:cursor-not-allowed disabled:opacity-60 sm:text-base"
                  >
                    {isPushingNotion ? "Saving notes to Notion..." : "Save AI + Timestamp Notes to Notion"}
                  </button>
                )}
              </div>
              {pushFeedback && (
                <p
                  className={`mt-3 text-sm ${
                    pushFeedback.type === "success" ? "text-[#2E7D57]" : "text-[#B34A4A]"
                  }`}
                >
                  {pushFeedback.message}
                </p>
              )}
            </div>

            {!results && !isProcessing ? (
              <motion.div
                key="guide"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3 }}
                className="h-full min-h-[60vh] p-4 sm:p-5"
              >
                <div className="w-full">
                  <div
                    className="w-full"
                    onMouseEnter={() => setIsGuideHovered(true)}
                    onMouseLeave={() => setIsGuideHovered(false)}
                  >
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={`guide-${guideIndex}`}
                        initial={{ opacity: 0, x: 26, scale: 0.985 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: -24, scale: 0.985 }}
                        transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
                        className="p-4 sm:p-6"
                      >
                        <div className="text-sm uppercase tracking-[0.14em] text-[#7A5BB5]">{guideSlides[guideIndex].eyebrow}</div>
                        <h3 className="mt-3 text-[2rem] font-[var(--font-space-grotesk)] leading-tight text-[#2C1F3E] sm:text-[2.15rem]">
                          {guideSlides[guideIndex].title}
                        </h3>
                        <p className="mt-6 text-sm uppercase tracking-[0.14em] text-[#8E7AAE]">Use Case</p>
                        <p className="mt-2 text-[1.03rem] leading-relaxed text-[#4D3D66] sm:text-lg">{guideSlides[guideIndex].useCase}</p>
                        <p className="mt-6 text-sm uppercase tracking-[0.14em] text-[#8E7AAE]">Why We Built This</p>
                        <div className="mt-2.5 space-y-2.5 text-[1.03rem] leading-relaxed text-[#4D3D66] sm:text-lg">
                          {guideSlides[guideIndex].reasonLines.map((line, idx) => (
                            <p key={idx}>{line}</p>
                          ))}
                        </div>
                      </motion.div>
                    </AnimatePresence>

                    <div className="mt-7 flex flex-wrap items-center justify-between gap-4">
                      <div className="flex items-center gap-2">
                        {guideSlides.map((_, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => setGuideIndex(idx)}
                            className={`h-2.5 rounded-full transition-all ${
                              idx === guideIndex ? "w-7 bg-[#7A5BB5]" : "w-2.5 bg-[#D7C9EF] hover:bg-[#C9B5EA]"
                            }`}
                            aria-label={`Go to guide slide ${idx + 1}`}
                          />
                        ))}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" className="px-3.5 py-2.5 text-base" onClick={goPrevGuide}>
                          &lt;- Prev
                        </Button>
                        <Button variant="outline" className="px-3.5 py-2.5 text-base" onClick={goNextGuide}>
                          Next -&gt;
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : viewMode === 'synthesis' ? (
              <motion.div
                key="synthesis"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3 }}
                className="p-2 sm:p-3"
              >
                <SynthesisMode />
              </motion.div>
            ) : (
              <AnimatePresence mode="wait">
                {isProcessing ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                  className="h-full min-h-[60vh] flex items-center justify-center p-8"
                >
                  <LoadingPanel stage={processingStage} />
                </motion.div>
              ) : (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-8 p-3 sm:p-4"
                >
                  {mode === "study" && (
                    <StudyModeView data={results} sourceUrl={url} />
                  )}
                  {mode === "work" && (
                    <WorkModeView data={results} sourceUrl={url} />
                  )}
                  {mode === "quick" && (
                    <QuickModeView data={results} sourceUrl={url} />
                  )}
                  <QnASection />
                </motion.div>
              )}
            </AnimatePresence>
            )}
          </div>
        </section>
      </div>
        </div>
      </div>
    </div>
  )
}
