"use client"

import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Button } from "@/components/ui/Button"
import { api } from "@/lib/api"
import { smartWatchAnalytics, smartWatchDeepAnalysis, smartWatchQuickCheck } from "@/lib/api"
import { useAppStore } from "@/lib/store"
import { SmartWatchDeepResult, SmartWatchMoment, SmartWatchQuickResult } from "@/lib/types"

type SmartState = "IDLE" | "QUESTION_INPUT" | "CHECKING" | "VERDICT_SHOWN" | "COMPLETE"

interface SmartWatchProps {
  videoUrl: string
  sessionId: string | null
}

const RECENT_KEY = "notionclip_smartwatch_recent_questions"
const ENABLED_KEY = "notionclip_smartwatch_enabled"

function extractYoutubeId(text: string) {
  const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/
  const match = text.match(regExp)
  return match && match[2].length === 11 ? match[2] : null
}

function loadRecent(): string[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((q) => typeof q === "string" && q.trim()).slice(0, 5)
  } catch {
    return []
  }
}

function saveRecent(question: string, current: string[]): string[] {
  const clean = question.trim()
  if (!clean) return current
  const next = [clean, ...current.filter((q) => q.toLowerCase() !== clean.toLowerCase())].slice(0, 5)
  if (typeof window !== "undefined") {
    localStorage.setItem(RECENT_KEY, JSON.stringify(next))
  }
  return next
}

function verdictStyles(verdict: string) {
  const v = verdict.toLowerCase()
  if (v === "watch") return "border-green-500/40 bg-gradient-to-br from-green-500/15 to-green-500/5 text-green-300"
  if (v === "skim") return "border-yellow-500/40 bg-gradient-to-br from-yellow-500/15 to-yellow-500/5 text-yellow-300"
  return "border-red-500/40 bg-gradient-to-br from-red-500/15 to-red-500/5 text-red-300"
}

function verdictIcon(verdict: string) {
  const v = verdict.toLowerCase()
  if (v === "watch") return "🟢"
  if (v === "skim") return "🟡"
  return "🔴"
}

function friendlyErrorText() {
  return "We couldn't analyse this video right now. Please try again in a moment."
}

export function SmartWatch({ videoUrl, sessionId }: SmartWatchProps) {
  const { userId, transcript, setTranscript, setDuration, setTranscriptCacheHit, setTranscriptFetchMs } = useAppStore()
  const [enabled, setEnabled] = useState<boolean>(true)
  const [localSessionId, setLocalSessionId] = useState<string | null>(null)
  const [question, setQuestion] = useState("")
  const [state, setState] = useState<SmartState>("IDLE")
  const [recentQuestions, setRecentQuestions] = useState<string[]>([])
  const [quickResult, setQuickResult] = useState<SmartWatchQuickResult | null>(null)
  const [deepResult, setDeepResult] = useState<SmartWatchDeepResult | null>(null)
  const [friendlyError, setFriendlyError] = useState("")
  const [checkingSince, setCheckingSince] = useState<number | null>(null)
  const [elapsedMs, setElapsedMs] = useState<number | null>(null)
  const [deepSlowNotice, setDeepSlowNotice] = useState(false)
  const [prefetchState, setPrefetchState] = useState<"idle" | "fetching" | "ready" | "error">("idle")

  useEffect(() => {
    setRecentQuestions(loadRecent())
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return
    const saved = window.localStorage.getItem(ENABLED_KEY)
    if (saved === "false") {
      setEnabled(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(ENABLED_KEY, enabled ? "true" : "false")
  }, [enabled])

  useEffect(() => {
    if (typeof window === "undefined") return
    let id = sessionId || window.localStorage.getItem("notionclip_session_id")
    if (!id) {
      id = crypto.randomUUID()
      window.localStorage.setItem("notionclip_session_id", id)
    }
    setLocalSessionId(id)
  }, [sessionId])

  // Auto-show question input when URL changes
  useEffect(() => {
    if (!enabled || !videoUrl) {
      setState("IDLE")
      setQuestion("")
      setQuickResult(null)
      setDeepResult(null)
      setFriendlyError("")
      setPrefetchState("idle")
      return
    }
    setState("QUESTION_INPUT")
  }, [videoUrl, enabled])

  useEffect(() => {
    if (!enabled || !videoUrl.trim()) {
      setPrefetchState("idle")
      return
    }
    const videoId = extractYoutubeId(videoUrl)
    if (!videoId) {
      setPrefetchState("error")
      return
    }

    let cancelled = false
    const prefetch = async () => {
      setPrefetchState("fetching")
      try {
        const started = Date.now()
        const transcriptRes = await api.getTranscript(videoId)
        if (cancelled) return
        const { transcript, duration_minutes, cache_hit, fetch_ms } = transcriptRes
        setTranscript(transcript)
        setDuration(duration_minutes || null)
        setTranscriptCacheHit(typeof cache_hit === "boolean" ? cache_hit : null)
        setTranscriptFetchMs(typeof fetch_ms === "number" ? fetch_ms : Date.now() - started)
        setPrefetchState("ready")
      } catch {
        if (!cancelled) {
          setPrefetchState("error")
        }
      }
    }

    void prefetch()
    return () => {
      cancelled = true
    }
  }, [enabled, videoUrl, setDuration, setTranscript, setTranscriptCacheHit, setTranscriptFetchMs])

  useEffect(() => {
    if (!checkingSince || state !== "CHECKING") {
      setElapsedMs(null)
      return
    }
    setElapsedMs(Math.max(0, Date.now() - checkingSince))
    const timer = window.setInterval(() => {
      setElapsedMs(Math.max(0, Date.now() - checkingSince))
    }, 250)
    return () => window.clearInterval(timer)
  }, [checkingSince, state])

  const effectiveSessionId = sessionId || localSessionId
  const canAnalyze = Boolean(effectiveSessionId && videoUrl.trim() && question.trim())

  const startDeepAnalysis = async (
    videoId: string,
    userQuestion: string,
    currentSessionId: string,
    verdict: "watch" | "skim" | "skip"
  ) => {
    setDeepSlowNotice(false)
    const slowTimer = setTimeout(() => {
      setDeepSlowNotice(true)
    }, 15000)

    try {
      const deep = await smartWatchDeepAnalysis(videoId, userQuestion, currentSessionId, verdict)
      setDeepResult(deep)
      setState("COMPLETE")
      void smartWatchAnalytics(currentSessionId, "smart_watch_timestamps_ready", userId, {
        video_id: videoId,
        moments_found: deep.total_relevant_moments,
        stage2_ms: deep.stage2_ms,
        prompt_version: deep.prompt_version || null,
      })
    } catch {
      setState("VERDICT_SHOWN")
    } finally {
      clearTimeout(slowTimer)
    }
  }

  const handleAnalyze = async () => {
    if (!effectiveSessionId || !videoUrl.trim() || !question.trim()) return

    setFriendlyError("")
    setQuickResult(null)
    setDeepResult(null)
    setState("CHECKING")
    setCheckingSince(Date.now())
    setRecentQuestions((prev) => saveRecent(question, prev))

    try {
      const quick = await smartWatchQuickCheck(videoUrl.trim(), question.trim(), effectiveSessionId, transcript)
      setQuickResult(quick)
      setCheckingSince(null)
      setState("VERDICT_SHOWN")
      void smartWatchAnalytics(effectiveSessionId, "smart_watch_verdict_shown", userId, {
        video_id: quick.video_id,
        verdict: quick.verdict,
        confidence: quick.confidence,
        stage1_ms: quick.stage1_ms,
        prompt_version: quick.prompt_version || null,
      })

      if (quick.verdict !== "skip") {
        void startDeepAnalysis(quick.video_id, question.trim(), effectiveSessionId, quick.verdict)
      }
    } catch {
      setCheckingSince(null)
      setFriendlyError(friendlyErrorText())
      setState("QUESTION_INPUT")
    }
  }

  const moments: SmartWatchMoment[] = deepResult?.relevant_moments || []

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-3 py-2">
        <div className="text-sm text-white/85">Smart Watch mode</div>
        <button
          type="button"
          onClick={() => setEnabled((v) => !v)}
          title={enabled ? "Disable Smart Watch pre-check" : "Enable Smart Watch pre-check"}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
            enabled ? "bg-primary" : "bg-white/20"
          }`}
          aria-pressed={enabled}
          aria-label="Toggle Smart Watch mode"
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-white transition ${
              enabled ? "translate-x-5" : "translate-x-1"
            }`}
          />
        </button>
      </div>

      {enabled && videoUrl && (
        <div className="text-xs text-white/60 px-1">
          {prefetchState === "fetching" && "Preparing transcript in background..."}
          {prefetchState === "ready" && "Transcript ready. Ask your question and get verdict fast."}
          {prefetchState === "error" && "Transcript prefetch failed. Verdict can still run."}
        </div>
      )}

      <AnimatePresence initial={false}>
        {enabled && state !== "IDLE" && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3"
          >
            <div className="text-xs font-semibold uppercase text-white/60 tracking-wide">🔍 Smart Watch Pre-Check</div>

            {state === "QUESTION_INPUT" && (
              <>
                <div className="text-sm text-white/90 font-medium">What is your focus question?</div>
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && canAnalyze && handleAnalyze()}
                  placeholder="e.g. What is the main concept? How does this work?"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/90 placeholder:text-white/35 focus:outline-none focus:border-white/20 transition-colors"
                  autoFocus
                />
                {recentQuestions.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs text-white/50">Recent questions</div>
                    <div className="flex flex-wrap gap-2">
                      {recentQuestions.map((q) => (
                        <button
                          key={q}
                          className="text-xs px-2.5 py-1 rounded-md border border-white/15 bg-white/5 hover:bg-white/10 text-white/80 transition-colors"
                          onClick={() => setQuestion(q)}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {friendlyError && <div className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{friendlyError}</div>}
                <Button
                  variant="outline"
                  className="w-full py-2.5 text-sm"
                  onClick={handleAnalyze}
                  disabled={!canAnalyze}
                  title="Analyze video for your question (5-10 seconds)"
                >
                  Get Smart Verdict →
                </Button>
              </>
            )}

            {state === "CHECKING" && (
              <div className="space-y-2 text-sm text-white/80">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-white/80 animate-pulse" />
                  <span>Reading transcript...</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-white/80 animate-pulse [animation-delay:180ms]" />
                  <span>Matching to your intent...</span>
                </div>
                {elapsedMs && elapsedMs > 1000 && (
                  <div className="text-xs text-white/55">{(elapsedMs / 1000).toFixed(1)}s elapsed</div>
                )}
              </div>
            )}

            {(state === "VERDICT_SHOWN" || state === "COMPLETE") && quickResult && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className={`rounded-xl border-2 p-4 space-y-3 ${verdictStyles(quickResult.verdict)}`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{verdictIcon(quickResult.verdict)}</span>
                  <div>
                    <div className="text-sm font-bold uppercase tracking-wider">{quickResult.verdict}</div>
                    <div className="text-xs opacity-80">Confidence: {Math.round(quickResult.confidence * 100)}%</div>
                  </div>
                </div>

                <div className="text-sm leading-relaxed italic">&ldquo;{quickResult.reason}&rdquo;</div>

                {quickResult.estimated_timestamp_range && (
                  <div className="text-xs opacity-80 bg-black/20 rounded-lg px-2 py-1.5">
                    💡 Answer likely at: {quickResult.estimated_timestamp_range}
                  </div>
                )}

                {quickResult.verdict !== "skip" && state === "VERDICT_SHOWN" && (
                  <div className="text-xs text-current/70">[Finding exact moments...]</div>
                )}

                {deepSlowNotice && state === "VERDICT_SHOWN" && (
                  <div className="text-xs opacity-70">🕐 Taking longer than usual...</div>
                )}

                {state === "COMPLETE" && moments.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-current/20">
                    <div className="text-xs font-semibold opacity-90">Relevant moments:</div>
                    <div className="flex flex-wrap gap-2">
                      {moments.map((m, idx) => (
                        <motion.a
                          key={`${m.timestamp_seconds}-${idx}`}
                          initial={{ opacity: 0, x: -6 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2, delay: idx * 0.04 }}
                          href={m.youtube_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={() => {
                            void smartWatchAnalytics(sessionId || "", "smart_watch_timestamp_clicked", userId, {
                              video_url: m.youtube_url,
                              timestamp_seconds: m.timestamp_seconds,
                            })
                          }}
                          title={m.quote}
                          className="text-xs px-2.5 py-1.5 rounded-full border border-current/40 bg-current/15 hover:bg-current/25 text-current transition-all font-medium"
                        >
                          ⏱️ {m.timestamp_display}
                        </motion.a>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs opacity-70 pt-2 border-t border-current/20">
                  ⚡ Analysed in {(quickResult.stage1_ms / 1000).toFixed(1)}s{state === "COMPLETE" ? ` • ${deepResult?.total_relevant_moments || 0} key moments` : ""}
                </div>

                {quickResult.verdict === "watch" && (
                  <Button
                    variant="default"
                    className="w-full mt-2 py-2 text-xs bg-current/30 hover:bg-current/40 border border-current/50"
                    onClick={() => setState("QUESTION_INPUT")}
                    title="Use the Process Video button below for full notes"
                  >
                    Verdict ready. Use Process Video for full notes.
                  </Button>
                )}

                <button
                  onClick={() => setState("QUESTION_INPUT")}
                  className="w-full text-xs text-current/70 hover:text-current py-1 transition-colors"
                >
                  Try different question
                </button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
