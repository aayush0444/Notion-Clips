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

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://notion-clips-production.up.railway.app"

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
  const { sessionId, userId } = useAppStore()
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
        const res = await fetch(`${API_BASE}/study-session/${studySessionId}${query}`)
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
    if (!canStart || !studentLevel || !sessionId) return
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
      setView("teaching")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to build study session.")
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
      <div className="space-y-6">
        <div className="surface-premium rounded-2xl p-6 space-y-3">
          <div className="text-xs uppercase tracking-wider text-slate-500">Start here</div>
          <div className="text-sm text-slate-900">{tutor.foundation}</div>
          <div className="text-xs text-slate-500">
            📍 Best explained in: {sourceTitle(tutor.foundation_source_index)}{" "}
            {tutor.foundation_timestamp_or_page}
          </div>
        </div>

        <div className="surface-premium rounded-2xl p-6 space-y-4">
          <div className="text-xs uppercase tracking-wider text-slate-500">Core Teaching</div>
          <div className="text-sm text-slate-800 whitespace-pre-line">{tutor.core_teaching}</div>
          <div className="flex flex-wrap gap-2">
            {tutor.core_citations.map((citation, idx) => {
              const type = sourceType(citation.source_index)
              const title = sourceTitle(citation.source_index)
              const timestamp = citation.timestamp_or_page
              const url = sourceUrl(citation.source_index)
              const seconds = timestampToSeconds(timestamp)
              const href =
                type === "youtube" && seconds !== null
                  ? `${url}${url.includes("?") ? "&" : "?"}t=${seconds}`
                  : url
              const icon = type === "youtube" ? "📹" : type === "pdf" ? "📄" : "🔗"
              return (
                <a
                  key={`${citation.source_index}-${idx}`}
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  title={citation.quote}
                  className="px-2.5 py-1 rounded-full border border-[#d8d0f4] bg-white/82 text-xs text-slate-700 hover:bg-[#f6f2ff]"
                >
                  {icon} {title} {timestamp}
                </a>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="surface-premium rounded-2xl p-5 border border-green-500/20 bg-green-500/5">
            <div className="text-xs uppercase tracking-wider text-green-700 mb-2">✓ Sources Agree</div>
            {knowledgeMap.agreements.length ? (
              <ul className="space-y-2 text-sm text-slate-700">
                {knowledgeMap.agreements.map((item, idx) => (
                  <li key={idx}>• {item}</li>
                ))}
              </ul>
            ) : (
              <div className="text-xs text-slate-600">
                Your sources cover distinct aspects — no direct overlaps found
              </div>
            )}
          </div>
          <div className="surface-premium rounded-2xl p-5 border border-yellow-500/20 bg-yellow-500/5">
            <div className="text-xs uppercase tracking-wider text-yellow-700 mb-2">⚠️ Sources Disagree</div>
            {knowledgeMap.contradictions.length ? (
              <div className="space-y-3 text-sm text-slate-700">
                {knowledgeMap.contradictions.map((c, idx) => (
                  <div key={idx}>
                    <div className="font-semibold">{c.topic}</div>
                    <div>Source A says: {c.source_a_says}</div>
                    <div>Source B says: {c.source_b_says}</div>
                    {c.resolution && <div className="italic text-slate-600">Most likely: {c.resolution}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-600">No contradictions detected.</div>
            )}
          </div>
        </div>

        <div className="surface-premium rounded-2xl p-5">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">Gaps in your sources</div>
          <ul className="space-y-2 text-sm text-slate-700">
            {knowledgeMap.knowledge_gaps.map((gap, idx) => (
              <li key={idx}>• {gap}</li>
            ))}
          </ul>
        </div>

        <div className="surface-premium rounded-2xl p-6 space-y-4">
          <div>
            <div className="text-sm text-slate-900">Test Your Understanding</div>
            <div className="text-xs text-slate-500">Answer all 3 questions to complete this session</div>
          </div>
          {visibleQuestions.map((q) => {
            const evaluation = q.evaluation
            const status =
              evaluation?.correct === "true"
                ? "border-green-500/30 bg-green-500/5"
                : evaluation?.correct === "partial"
                ? "border-yellow-500/30 bg-yellow-500/5"
                : evaluation?.correct === "false"
                ? "border-red-500/30 bg-red-500/5"
                : "border-[#ddd4f6] bg-white/82"
            return (
              <div key={q.id} className={`rounded-xl border p-4 space-y-3 ${status}`}>
                <div className="flex flex-wrap gap-2 text-xs text-slate-600">
                  <span className="px-2 py-0.5 rounded-full border border-[#d8d0f4]">
                    {q.difficulty.toUpperCase()}
                  </span>
                  <span className="px-2 py-0.5 rounded-full border border-[#d8d0f4]">
                    {q.type.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-slate-900">{q.question}</div>
                {!q.answered && (
                  <>
                    <textarea
                      value={q.user_answer || ""}
                      onChange={(e) => {
                        const answer = e.target.value
                        setSessionData((prev) => {
                          if (!prev || !prev.tutor_output) return prev
                          const updated = prev.tutor_output.knowledge_check.map((item) =>
                            item.id === q.id ? { ...item, user_answer: answer } : item
                          )
                          return {
                            ...prev,
                            tutor_output: { ...prev.tutor_output, knowledge_check: updated },
                          }
                        })
                      }}
                      placeholder="Type your answer here..."
                      className="w-full min-h-[120px] bg-white/80 border border-[#ddd4f6] rounded-lg px-3 py-2 text-sm text-slate-800"
                    />
                    <button
                      type="button"
                      disabled={evaluatingId === q.id || !q.user_answer?.trim()}
                      onClick={() => handleSubmitAnswer(q)}
                      className="px-4 py-2 rounded-lg border border-[#ddd4f6] bg-white/80 text-sm text-slate-700 hover:bg-[#f6f2ff] disabled:opacity-50"
                    >
                      {evaluatingId === q.id ? "Evaluating..." : "Submit Answer"}
                    </button>
                  </>
                )}
                {q.answered && evaluation && (
                  <div className="text-xs text-slate-700 space-y-2">
                    <div>
                      {evaluation.correct === "true" && `✓ ${evaluation.feedback}`}
                      {evaluation.correct === "partial" && `◐ ${evaluation.feedback}`}
                      {evaluation.correct === "false" && `✗ ${evaluation.feedback}`}
                    </div>
                    {evaluation.misconception && <div>⚠️ Misconception: {evaluation.misconception}</div>}
                    {evaluation.correction && <div>✓ Correction: {evaluation.correction}</div>}
                    <div>
                      Confirmed by: {sourceTitle(evaluation.cited_source_index)}{" "}
                      {findTimestampForSource(evaluation.cited_source_index)}
                    </div>
                  </div>
                )}
              </div>
            )
          })}

          {questions.length > 0 && questions.every((q) => q.answered) && (
            <div className="border border-[#ddd4f6] rounded-xl p-4 bg-white/82 space-y-2">
              <div className="text-sm text-slate-900">🎓 Session Complete</div>
              <div className="text-xs text-slate-600">
                Score: {score.correct}/3 correct, {score.partial}/3 partial
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleNotionSave}
                  className="px-3 py-2 rounded-lg border border-[#ddd4f6] bg-white/80 text-xs text-slate-700 hover:bg-[#f6f2ff]"
                >
                  💾 Save to Notion
                </button>
                <button
                  type="button"
                  onClick={resetSession}
                  className="px-3 py-2 rounded-lg border border-[#ddd4f6] bg-white/80 text-xs text-slate-700 hover:bg-[#f6f2ff]"
                >
                  🔄 New Session
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleNotionSave}
            className="px-4 py-2 rounded-lg border border-[#ddd4f6] bg-white/80 text-sm text-slate-700 hover:bg-[#f6f2ff]"
          >
            💾 Save to Notion
          </button>
          <button
            type="button"
            onClick={() => {
              const confirmed = window.confirm("Leave this session and return to setup?")
              if (confirmed) resetSession()
            }}
            className="px-4 py-2 rounded-lg border border-[#ddd4f6] bg-white/80 text-sm text-slate-700 hover:bg-[#f6f2ff]"
          >
            ← Back to Setup
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="surface-premium rounded-2xl p-4 space-y-4 sm:p-5">
      <div className="space-y-2">
        <label className="text-xs text-slate-500 uppercase tracking-wider">
          What do you want to understand deeply?
        </label>
        <textarea
          value={learningGoal}
          onChange={(e) => setLearningGoal(e.target.value)}
          placeholder="e.g. I want to deeply understand how transformer attention actually works"
          className="w-full min-h-[104px] bg-white/80 border border-[#ddd4f6] rounded-lg px-3 py-2 text-sm text-slate-800"
        />
      </div>

      <div className="space-y-2">
        <div className="text-xs text-slate-500 uppercase tracking-wider">
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
              className={`px-3 py-2 rounded-lg text-xs border ${
                studentLevel === level.key
                  ? "bg-white text-black border-white"
                  : "border-[#ddd4f6] bg-white/80 text-slate-700"
              }`}
            >
              {level.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2.5">
        <div className="text-xs text-slate-500 uppercase tracking-wider">Add your sources (2–4)</div>
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
              className="bg-white/80 border border-[#ddd4f6] rounded-lg px-2 py-2 text-xs text-slate-700"
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
                  })
                }
                className="text-xs text-slate-700"
              />
            ) : (
              <input
                type="text"
                value={source.url}
                onChange={(e) =>
                  handleSourceChange(source.id, {
                    url: e.target.value,
                  })
                }
                placeholder={source.type === "youtube" ? "YouTube URL" : "Article URL"}
                className="flex-1 bg-white/80 border border-[#ddd4f6] rounded-lg px-3 py-2 text-xs text-slate-700"
              />
            )}
            {sources.length > 2 && (
              <button
                type="button"
                onClick={() => handleRemoveSource(source.id)}
                className="text-xs text-red-600 hover:text-red-700"
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
          className="text-xs text-slate-700 hover:text-slate-900 disabled:text-slate-300"
        >
          + Add another source
        </button>
      </div>

      {error && <div className="text-xs text-red-600">{error}</div>}

      <button
        type="button"
        disabled={!canStart}
        onClick={handleStartSession}
        className="w-full px-4 py-3 rounded-lg border border-[#ddd4f6] bg-white text-black text-sm disabled:opacity-50"
      >
        🎓 Start Learning Session
      </button>
    </div>
  )
}


