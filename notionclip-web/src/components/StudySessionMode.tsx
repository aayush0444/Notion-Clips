"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AnswerEvaluationResponse,
  KnowledgeCheckQuestion,
  KnowledgeMap,
  StudySession,
  StudySource,
  TutorOutput,
} from "@/lib/types"
import {
  addPdfToSession,
  buildStudySession,
  createStudySession,
  pushStudySessionToNotion,
  submitAnswer,
} from "@/lib/api"
import { backendUrl } from "@/lib/backendUrl"
import { useAppStore } from "@/lib/store"

type SourceType = "youtube" | "article" | "pdf"
type StudentLevel = "beginner" | "some_background" | "advanced"

type SourceInput = {
  id: string
  type: SourceType
  url: string
  file: File | null
}

type ViewState = "setup" | "building" | "teaching" | "complete"

function createEmptySource(type: SourceType = "youtube"): SourceInput {
  return {
    id: crypto.randomUUID(),
    type,
    url: "",
    file: null,
  }
}

function timestampToSeconds(timestamp: string): number | null {
  const parts = timestamp.split(":").map((p) => Number(p))
  if (parts.some((p) => Number.isNaN(p))) return null
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return null
}

export function StudySessionMode() {
  const { sessionId, userId, setResults } = useAppStore()
  const [view, setView] = useState<ViewState>("setup")
  const [learningGoal, setLearningGoal] = useState("")
  const [studentLevel, setStudentLevel] = useState<StudentLevel | null>(null)
  const [sources, setSources] = useState<SourceInput[]>([
    createEmptySource("youtube"),
    createEmptySource("article"),
  ])
  const [studySessionId, setStudySessionId] = useState<string | null>(null)
  const [sessionData, setSessionData] = useState<StudySession | null>(null)
  const [error, setError] = useState("")
  const [buildingNotice, setBuildingNotice] = useState(false)
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null)
  const [notionUrl, setNotionUrl] = useState<string | null>(null)

  useEffect(() => {
    if (view !== "building") return
    setBuildingNotice(false)
    const timer = setTimeout(() => setBuildingNotice(true), 10000)
    return () => clearTimeout(timer)
  }, [view])

  useEffect(() => {
    if (view !== "building" || !studySessionId) return
    let active = true
    const poll = async () => {
      try {
        const query = userId ? `?user_id=${encodeURIComponent(userId)}` : ""
        const res = await fetch(backendUrl(`/study-session/${studySessionId}${query}`))
        if (!res.ok) return
        const data = (await res.json()) as StudySession
        if (!active) return
        setSessionData(data)
        if (data.status === "ready") {
          setView("teaching")
        }
      } catch {
        // ignore polling errors
      }
    }
    poll()
    const interval = setInterval(poll, 3000)
    return () => {
      active = false
      clearInterval(interval)
    }
  }, [view, studySessionId, userId])

  const canStart = useMemo(() => {
    if (!sessionId) return false
    if (learningGoal.trim().length < 10) return false
    if (!studentLevel) return false
    if (sources.length < 2 || sources.length > 4) return false
    for (const source of sources) {
      if (source.type === "pdf" && !source.file) return false
      if (source.type !== "pdf" && !source.url.trim()) return false
    }
    return true
  }, [learningGoal, sessionId, studentLevel, sources])

  const handleAddSource = () => {
    if (sources.length >= 4) return
    setSources((prev) => [...prev, createEmptySource("youtube")])
  }

  const handleRemoveSource = (id: string) => {
    if (sources.length <= 2) return
    setSources((prev) => prev.filter((s) => s.id !== id))
  }

  const handleSourceChange = (id: string, updates: Partial<SourceInput>) => {
    setSources((prev) =>
      prev.map((s) => (s.id === id ? { ...s, ...updates } : s))
    )
  }

  const handleStartSession = async () => {
    if (!canStart || !studentLevel || !sessionId) {
      // Explicit validation check for better UX
      for (const source of sources) {
        if (source.type === "pdf" && !source.file) {
          setError("Please upload a PDF file for all PDF sources.")
          return
        }
        if (source.type !== "pdf" && (!source.url || !source.url.trim())) {
          setError(`Please provide a valid URL for your ${source.type} source.`)
          return
        }
      }
      if (learningGoal.trim().length < 10) {
        setError("Please describe your learning goal in more detail (min 10 chars).")
        return
      }
      if (!studentLevel) {
        setError("Please select your current level.")
        return
      }
      return
    }
    setError("")
    setView("building")
    try {
      const payloadSources = sources.map((s) => ({
        type: s.type,
        url: s.type === "pdf" ? s.file?.name || "document.pdf" : s.url,
      }))
      const created = await createStudySession(
        learningGoal.trim(),
        studentLevel,
        payloadSources,
        sessionId,
        userId || undefined
      )
      setStudySessionId(created.study_session_id)

      const pdfSources = sources.filter((s) => s.type === "pdf" && s.file)
      for (const pdf of pdfSources) {
        await addPdfToSession(created.study_session_id, pdf.file as File)
      }

      const built = await buildStudySession(
        created.study_session_id,
        sessionId,
        userId || undefined
      )
      setSessionData(built)
      setResults(built)
      setView("teaching")
    } catch (err: any) {
      console.error("Build failed:", err)
      setError(err.message || "Failed to build study session")
      setView("setup")
    }
  }

  const handleSubmitAnswer = async (question: KnowledgeCheckQuestion) => {
    if (!studySessionId || !sessionId) return
    if (!question.user_answer) return
    setEvaluatingId(question.id)
    try {
      const response: AnswerEvaluationResponse = await submitAnswer(
        studySessionId,
        question.id,
        question.user_answer,
        sessionId,
        userId || undefined
      )
      setSessionData((prev) => {
        if (!prev || !prev.tutor_output) return prev
        const updatedQuestions = prev.tutor_output.knowledge_check.map((q) =>
          q.id === response.question_id
            ? {
                ...q,
                answered: true,
                evaluation: response.evaluation,
              }
            : q
        )
        return {
          ...prev,
          tutor_output: { ...prev.tutor_output, knowledge_check: updatedQuestions },
        }
      })
    } finally {
      setEvaluatingId(null)
    }
  }

  const handleNotionSave = async () => {
    if (!studySessionId || !sessionId) return
    setError("")
    try {
      const result = await pushStudySessionToNotion(studySessionId, sessionId, userId || undefined)
      setNotionUrl(result.notion_url)
      setView("complete")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save to Notion.")
    }
  }

  const resetSession = () => {
    setView("setup")
    setLearningGoal("")
    setStudentLevel(null)
    setSources([createEmptySource("youtube"), createEmptySource("article")])
    setStudySessionId(null)
    setSessionData(null)
    setError("")
    setNotionUrl(null)
    setResults(null)
  }

  const tutor: TutorOutput | null = sessionData?.tutor_output || null
  const knowledgeMap: KnowledgeMap | null = sessionData?.knowledge_map || null
  const sessionSources: StudySource[] = sessionData?.sources || []
  const questions = useMemo(() => tutor?.knowledge_check || [], [tutor])
  const nextQuestionIndex = questions.findIndex((q) => !q.answered)
  const visibleQuestions =
    nextQuestionIndex === -1 ? questions : questions.slice(0, nextQuestionIndex + 1)

  const score = useMemo(() => {
    const correct = questions.filter((q) => q.evaluation?.correct === "true").length
    const partial = questions.filter((q) => q.evaluation?.correct === "partial").length
    return { correct, partial }
  }, [questions])

  const sourceTitle = (idx: number) => {
    const source = sessionSources.find((s) => s.source_index === idx)
    return source?.title || source?.url_or_filename || `Source ${idx}`
  }

  const sourceType = (idx: number) => {
    const source = sessionSources.find((s) => s.source_index === idx)
    return source?.type || "article"
  }

  const sourceUrl = (idx: number) => {
    const source = sessionSources.find((s) => s.source_index === idx)
    return source?.url_or_filename || ""
  }

  const findTimestampForSource = (idx: number) => {
    const concept = knowledgeMap?.concepts.find((c) => c.best_source_index === idx)
    return concept?.timestamp_or_page || ""
  }

  if (view === "complete") {
    return (
      <div className="surface-premium rounded-2xl p-6 space-y-4">
        <div className="text-green-700 text-sm">✓ Study session saved to Notion</div>
        {notionUrl && (
          <a
            href={notionUrl}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-primary underline"
          >
            Open Notion page
          </a>
        )}
        <button
          type="button"
          onClick={resetSession}
          className="px-4 py-2 rounded-lg border border-[#ddd4f6] bg-white/80 text-sm text-slate-700 hover:bg-[#f6f2ff]"
        >
          Start New Session
        </button>
      </div>
    )
  }

  if (view === "building") {
    return (
      <div className="surface-premium rounded-2xl p-6 space-y-4">
        <div className="text-sm text-slate-700">Building your study session...</div>
        <div className="space-y-2 text-sm text-slate-700">
          <div className="font-medium text-slate-800">Reading your sources...</div>
          {(sessionData?.sources || sources.map((s, idx) => ({
            source_index: idx,
            type: s.type,
            title: s.type === "pdf" ? s.file?.name || "PDF" : s.url,
            url_or_filename: s.type === "pdf" ? s.file?.name || "PDF" : s.url,
            extraction_status: "pending",
          }))).map((source) => (
            <div key={source.source_index} className="text-xs">
              {source.extraction_status === "done" && `✓ ${source.title}`}
              {source.extraction_status === "failed" && `✗ ${source.title} — could not read`}
              {source.extraction_status === "pending" && `⟳ ${source.title}`}
            </div>
          ))}
        </div>
        <div className="text-xs text-slate-600">⟳ Building knowledge map across sources...</div>
        <div className="text-xs text-slate-600">⟳ Preparing your personal tutor...</div>
        {buildingNotice && (
          <div className="text-xs text-slate-500">
            Building your session usually takes 15–30 seconds depending on source length.
          </div>
        )}
      </div>
    )
  }

  if (view === "teaching" && tutor && knowledgeMap) {
    return (
      <div className="bg-[#F5F2FD] border border-[#7A5BB5]/20 rounded-xl p-5 text-center space-y-3">
        <div className="text-2xl">🧠</div>
        <p className="text-sm font-bold text-[#3D344D]">Study Session Ready</p>
        <p className="text-xs text-[#7A5BB5] font-medium leading-relaxed">
          Your personal teaching plan and knowledge map are now available in the main canvas.
        </p>
        <button
          onClick={resetSession}
          className="w-full py-2 rounded-lg border border-[#7A5BB5] text-[#7A5BB5] text-xs font-bold hover:bg-[#7A5BB5] hover:text-white transition-all"
        >
          Start New Session
        </button>
      </div>
    )
  }

  return (
    <div className="surface-premium rounded-2xl p-4 space-y-4 sm:p-5">
      <div className="space-y-3">
        <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2 mb-4 block">
          What do you want to understand deeply?
        </label>
        <textarea
          value={learningGoal}
          onChange={(e) => setLearningGoal(e.target.value)}
          placeholder="e.g. I want to deeply understand how transformer attention actually works"
          className="w-full min-h-[104px] bg-white border border-[#E8E0F0] rounded-xl px-4 py-3 text-[1.02rem] text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-[#CDBAEF] transition-all shadow-sm"
        />
      </div>

      <div className="space-y-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2 mb-4 block">
          Your current level with this topic
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { key: "beginner", label: "Complete Beginner" },
            { key: "some_background", label: "Some Background" },
            { key: "advanced", label: "Already Advanced" },
          ].map((level) => (
            <button
              key={level.key}
              type="button"
              onClick={() => setStudentLevel(level.key as StudentLevel)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                studentLevel === level.key
                  ? "bg-[#7A5BB5] text-white shadow-md border border-[#7A5BB5]"
                  : "bg-white border border-[#E8E0F0] text-foreground hover:border-[#7A5BB5] hover:text-[#7A5BB5]"
              }`}
            >
              {level.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2 mb-4 block">Add your sources (2–4)</div>
        {sources.map((source) => (
          <div key={source.id} className="flex flex-wrap items-center gap-2">
            <select
              value={source.type}
              onChange={(e) =>
                handleSourceChange(source.id, {
                  type: e.target.value as SourceType,
                  url: "",
                  file: null,
                })
              }
              className="bg-white border border-[#E8E0F0] rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-[#7A5BB5] focus:ring-1 focus:ring-[#7A5BB5] transition-colors"
            >
              <option value="youtube">YouTube</option>
              <option value="article">Article</option>
              <option value="pdf">PDF</option>
            </select>
            {source.type === "pdf" ? (
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(e) =>
                  handleSourceChange(source.id, {
                    file: e.target.files?.[0] || null,
                    url: ""
                  })
                }
                className="text-sm text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-[#F0EBF8] file:text-[#7A5BB5] hover:file:bg-[#E8E0F0]"
              />
            ) : (
              <input
                type="text"
                value={source.url || ""}
                onChange={(e) =>
                  handleSourceChange(source.id, {
                    url: e.target.value,
                    file: null
                  })
                }
                placeholder={source.type === "youtube" ? "YouTube URL" : "Article URL"}
                className="flex-1 bg-white border border-[#E8E0F0] rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-[#7A5BB5] focus:ring-1 focus:ring-[#7A5BB5] transition-colors"
              />
            )}
            {sources.length > 2 && (
              <button
                type="button"
                onClick={() => handleRemoveSource(source.id)}
                className="text-sm text-[#A0527A] hover:text-[#7d3b5b] p-2"
              >
                ✕
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          disabled={sources.length >= 4}
          onClick={handleAddSource}
          className="flex items-center gap-1.5 text-sm font-medium text-[#7A5BB5] hover:text-[#5B428A] disabled:text-slate-300 disabled:cursor-not-allowed transition-colors"
        >
          <span>+</span> Add another source
        </button>
      </div>

      {error && <div className="text-xs text-red-600">{error}</div>}

      <button
        type="button"
        disabled={!canStart}
        onClick={handleStartSession}
        className="w-full h-12 rounded-xl bg-[#7A5BB5] flex items-center justify-center text-white font-bold text-[16px] transition-all hover:bg-[#6847a1] active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Start Learning Session 🧠
      </button>
    </div>
  )
}


