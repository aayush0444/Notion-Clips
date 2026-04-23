"use client"

import { useMemo, useState } from "react"
import {
  AnswerEvaluationResponse,
  KnowledgeCheckQuestion,
  KnowledgeMap,
  StudySession,
  StudySource,
  TutorOutput,
} from "@/lib/types"
import {
  pushStudySessionToNotion,
  submitAnswer,
} from "@/lib/api"
import { useAppStore } from "@/lib/store"

function timestampToSeconds(timestamp: string): number | null {
  const parts = timestamp.split(":").map((p) => Number(p))
  if (parts.some((p) => Number.isNaN(p))) return null
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return null
}

export function StudySessionResultsView({ data }: { data: StudySession }) {
  const { sessionId, userId, setResults } = useAppStore()
  
  // States
  const [isSaving, setIsSaving] = useState(false)
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null)
  const [error, setError] = useState("")
  const [notionUrl, setNotionUrl] = useState<string | null>(null)
  const [isSaved, setIsSaved] = useState(false)

  const tutor: TutorOutput | null = data.tutor_output || null
  const knowledgeMap: KnowledgeMap | null = data.knowledge_map || null
  const sessionSources: StudySource[] = data.sources || []
  
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

  const handleSubmitAnswer = async (question: KnowledgeCheckQuestion) => {
    if (!data.study_session_id || !sessionId) return
    if (!question.user_answer) return
    setEvaluatingId(question.id)
    try {
      const response: AnswerEvaluationResponse = await submitAnswer(
        data.study_session_id,
        question.id,
        question.user_answer,
        sessionId,
        userId || undefined
      )
      
      // Update global results with immutable patterns
      const updatedData = { 
        ...data,
        tutor_output: data.tutor_output ? {
          ...data.tutor_output,
          knowledge_check: data.tutor_output.knowledge_check.map((q) =>
            q.id === response.question_id
              ? { ...q, answered: true, evaluation: response.evaluation }
              : q
          )
        } : data.tutor_output
      }
      setResults(updatedData)
    } finally {
      setEvaluatingId(null)
    }
  }

  const handleNotionSave = async () => {
    if (!data.study_session_id || !sessionId || isSaving) return
    setError("")
    setIsSaving(true)
    try {
      const result = await pushStudySessionToNotion(data.study_session_id, sessionId, userId || undefined)
      setNotionUrl(result.notion_url)
      setIsSaved(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save to Notion.")
    } finally {
      setIsSaving(false)
    }
  }

  if (!tutor || !knowledgeMap) return null

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {isSaved && (
        <div className="bg-[#E9F7EF] border border-[#2E7D57]/20 rounded-2xl p-6 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <span className="text-xl">✅</span>
            <div>
              <p className="text-sm font-bold text-[#1B5E20]">Study session saved to Notion</p>
              {notionUrl && (
                <a href={notionUrl} target="_blank" rel="noreferrer" className="text-xs text-[#2E7D57] underline hover:text-[#1B5E20]">
                  Open Notion page ↗
                </a>
              )}
            </div>
          </div>
          <button onClick={() => setResults(null)} className="text-xs font-bold text-[#2E7D57] hover:underline">
            Done
          </button>
        </div>
      )}

      <div className="bg-white border border-[#E4D9F5] rounded-2xl p-7 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-[#7A5BB5]">
          <span className="text-lg">📍</span>
          <p className="text-[11px] uppercase font-bold tracking-widest">Foundational Concept</p>
        </div>
        <p className="text-lg font-medium text-[#3D344D] leading-relaxed italic">"{tutor.foundation}"</p>
        <div className="pt-3 border-t border-[#F0EBF8]">
          <p className="text-xs text-[#7D748C]">
            Best explained in <span className="font-bold text-[#7A5BB5]">{sourceTitle(tutor.foundation_source_index)}</span> {tutor.foundation_timestamp_or_page}
          </p>
        </div>
      </div>

      <div className="bg-white border border-[#E4D9F5] rounded-2xl p-7 shadow-sm space-y-6">
        <div className="flex items-center gap-2 text-[#7A5BB5]">
          <span className="text-lg">🧠</span>
          <p className="text-[11px] uppercase font-bold tracking-widest">Core Teaching</p>
        </div>
        <div className="text-[16px] text-[#4D3D66] leading-loose whitespace-pre-wrap font-medium">
          {tutor.core_teaching}
        </div>
        <div className="flex flex-wrap gap-2 pt-4">
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
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-[#E8E0F0] bg-[#F9F8FF] text-xs font-bold text-[#5E4496] transition hover:bg-[#F0EBF8] hover:border-[#7A5BB5]/30 shadow-sm"
              >
                <span>{icon}</span>
                <span>{title}</span>
                <span className="opacity-60">{timestamp}</span>
              </a>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#E9F7EF]/50 border border-[#2E7D57]/20 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-2 text-[#2E7D57] mb-4">
            <span className="text-lg">✓</span>
            <p className="text-[11px] uppercase font-bold tracking-widest">Sources Agree</p>
          </div>
          {knowledgeMap.agreements.length ? (
            <ul className="space-y-3">
              {knowledgeMap.agreements.map((item, idx) => (
                <li key={idx} className="flex gap-2 text-sm text-[#2E7D57] font-medium leading-relaxed">
                  <span className="opacity-40">•</span> {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-[#2E7D57]/60 italic">Your sources cover distinct aspects — no direct overlaps found.</p>
          )}
        </div>

        <div className="bg-[#FFF9F2]/50 border border-[#D97706]/20 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-2 text-[#D97706] mb-4">
            <span className="text-lg">⚠️</span>
            <p className="text-[11px] uppercase font-bold tracking-widest">Sources Disagree</p>
          </div>
          {knowledgeMap.contradictions.length ? (
            <div className="space-y-5">
              {knowledgeMap.contradictions.map((c, idx) => (
                <div key={idx} className="space-y-2">
                  <p className="text-sm font-bold text-[#92400E]">{c.topic}</p>
                  <div className="space-y-1.5 border-l-2 border-[#D97706]/10 pl-3">
                    <p className="text-xs text-[#92400E]"><span className="opacity-60">Source A:</span> {c.source_a_says}</p>
                    <p className="text-xs text-[#92400E]"><span className="opacity-60">Source B:</span> {c.source_b_says}</p>
                  </div>
                  {c.resolution && (
                    <p className="text-xs italic text-[#92400E]/70 pt-1">
                      <span className="font-bold not-italic">Verdict:</span> {c.resolution}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#D97706]/60 italic">No contradictions detected between your sources.</p>
          )}
        </div>
      </div>

      <div className="bg-white border border-[#E4D9F5] rounded-2xl p-7 shadow-sm space-y-5">
        <div className="flex items-center gap-2 text-[#7A5BB5]">
          <span className="text-lg">🎯</span>
          <p className="text-[11px] uppercase font-bold tracking-widest">Key Concepts</p>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {knowledgeMap.concepts.map((concept, idx) => (
            <div key={idx} className="group p-5 rounded-2xl border border-[#F0EBF8] hover:border-[#7A5BB5]/20 hover:bg-[#F9F8FF] transition-all">
              <h4 className="text-[15px] font-bold text-[#3D344D]">{concept.concept_name}</h4>
              <p className="mt-2 text-sm text-[#7D748C] leading-relaxed font-medium">{concept.best_explanation}</p>
              <div className="mt-3 flex items-center gap-2">
                <span className="text-[10px] text-[#7A5BB5] bg-[#F5F2FD] px-2 py-0.5 rounded-md font-bold uppercase tracking-wider">
                  📍 {sourceTitle(concept.best_source_index)} {concept.timestamp_or_page}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 
      <div className="bg-white border border-[#E4D9F5] rounded-2xl p-7 shadow-sm space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[#7A5BB5]">
            <span className="text-lg">❓</span>
            <p className="text-[11px] uppercase font-bold tracking-widest">Knowledge Check</p>
          </div>
          <div className="text-[10px] font-bold text-[#9B7FD4] uppercase tracking-widest bg-gray-50 px-2.5 py-1 rounded-full">
            {questions.filter(q => q.answered).length} / {questions.length} Answered
          </div>
        </div>

        <div className="space-y-8">
          {visibleQuestions.map((q) => (
            <QuestionSection 
              key={q.id} 
              q={q} 
              data={data} 
              questions={questions}
              evaluatingId={evaluatingId}
              handleSubmitAnswer={handleSubmitAnswer}
              setResults={setResults}
              sourceTitle={sourceTitle}
              findTimestampForSource={findTimestampForSource}
            />
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-[#FAEFF5]/50 border border-[#A0527A]/20 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 text-[#A0527A] mb-4">
              <span className="text-lg">🔍</span>
              <p className="text-[11px] uppercase font-bold tracking-widest">Knowledge Gaps</p>
            </div>
            {knowledgeMap.knowledge_gaps.length ? (
              <ul className="space-y-3">
                {knowledgeMap.knowledge_gaps.map((gap, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-[#83214F] font-medium leading-relaxed">
                    <span className="opacity-40">•</span> {gap}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-[#A0527A]/60 italic">Your sources seem to cover the topic comprehensively.</p>
            )}
          </div>

          <div className="bg-[#F5F2FD] border border-[#7A5BB5]/20 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 text-[#7A5BB5] mb-4">
              <span className="text-lg">🚀</span>
              <p className="text-[11px] uppercase font-bold tracking-widest">Next Steps</p>
            </div>
            {tutor.next_steps.length ? (
              <ol className="space-y-3 list-decimal list-inside">
                {tutor.next_steps.map((step, idx) => (
                  <li key={idx} className="text-sm text-[#4D3D66] font-medium leading-relaxed pl-1 marker:text-[#7A5BB5] marker:font-bold">
                    {step}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-xs text-[#7A5BB5]/60 italic">Continue practicing these core concepts to master the topic.</p>
            )}
          </div>
        </div>

        {questions.length > 0 && questions.every((q) => q.answered) && (
          <div className="p-7 rounded-2xl bg-[#F5F2FD] border border-[#7A5BB5]/20 text-center space-y-4">
            <span className="text-4xl">🎓</span>
            <h3 className="text-xl font-bold text-[#3D344D]">Session Complete!</h3>
            <p className="text-sm text-[#7D748C] font-medium">
              Score: <span className="text-[#1B5E20] font-bold">{score.correct} correct</span>, <span className="text-[#D97706] font-bold">{score.partial} partial</span>
            </p>
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={handleNotionSave}
                disabled={isSaving}
                className="px-6 py-2.5 rounded-xl bg-white border border-[#7A5BB5] text-[#7A5BB5] text-sm font-bold shadow-sm hover:bg-[#F9F8FF] transition-all disabled:opacity-50"
              >
                {isSaving ? "💾 Saving..." : "💾 Save to Notion"}
              </button>
              <button
                onClick={() => setResults(null)}
                className="px-6 py-2.5 rounded-xl bg-[#7A5BB5] text-white text-sm font-bold shadow-sm hover:bg-[#6847a1] transition-all"
              >
                🔄 New Session
              </button>
            </div>
          </div>
        )}
      </div>
      */}

      {!isSaved && (
        <div className="flex items-center gap-4 pt-4">
          <button
            onClick={handleNotionSave}
            disabled={isSaving}
            className="flex-1 h-12 rounded-xl bg-[#7A5BB5] text-white font-bold flex items-center justify-center gap-2 shadow-lg hover:bg-[#6847a1] transition-all active:scale-95 disabled:opacity-50"
          >
            {isSaving ? "💾 Saving to Notion..." : "💾 Save results to Notion"}
          </button>
          <button
            onClick={() => setResults(null)}
            className="px-6 h-12 rounded-xl border border-[#E8E0F0] text-[#7D748C] font-bold hover:bg-[#F9F8FF] transition-all"
          >
            ← Back to Setup
          </button>
        </div>
      )}
      
      {error && <p className="text-sm text-center text-[#A0527A] font-medium">{error}</p>}
    </div>
  )
}

function QuestionSection({ 
  q, 
  data, 
  questions, 
  evaluatingId, 
  handleSubmitAnswer, 
  setResults,
  sourceTitle,
  findTimestampForSource 
}: { 
  q: KnowledgeCheckQuestion, 
  data: StudySession, 
  questions: KnowledgeCheckQuestion[],
  evaluatingId: string | null,
  handleSubmitAnswer: (q: KnowledgeCheckQuestion) => Promise<void>,
  setResults: (data: StudySession | null) => void,
  sourceTitle: (idx: number) => string,
  findTimestampForSource: (idx: number) => string
}) {
  const [localAnswer, setLocalAnswer] = useState(q.user_answer || "")
  const evaluation = q.evaluation
  const isEvaluating = evaluatingId === q.id
  const isAnswered = q.answered && evaluation

  // Update store only when we finish typing or submit
  const syncAnswer = (val: string) => {
    const updatedData = { 
      ...data,
      tutor_output: data.tutor_output ? {
        ...data.tutor_output,
        knowledge_check: data.tutor_output.knowledge_check.map((item) =>
          item.id === q.id ? { ...item, user_answer: val } : item
        )
      } : data.tutor_output
    }
    setResults(updatedData)
  }

  return (
    <div key={q.id} className="relative space-y-4 animate-in fade-in slide-in-from-left-4 duration-300">
      <div className="flex items-center gap-3">
        <span className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold ${
          isAnswered ? "bg-[#7A5BB5] text-white" : "bg-[#F5F2FD] text-[#7A5BB5]"
        }`}>
          {questions.indexOf(q) + 1}
        </span>
        <div className="flex gap-2">
          <span className="text-[9px] uppercase font-bold tracking-[0.1em] px-2 py-0.5 rounded-md bg-[#F9F8FF] text-[#7A5BB5] border border-[#7A5BB5]/10">
            {q.difficulty}
          </span>
          <span className="text-[9px] uppercase font-bold tracking-[0.1em] px-2 py-0.5 rounded-md bg-[#F9F8FF] text-[#7A5BB5] border border-[#7A5BB5]/10">
            {q.type}
          </span>
        </div>
      </div>
      
      <h4 className="text-[16px] font-bold text-[#3D344D] leading-snug">
        {q.question}
      </h4>

      {!q.answered || !evaluation ? (
        <div className="space-y-3">
          <textarea
            value={localAnswer}
            onChange={(e) => setLocalAnswer(e.target.value)}
            onBlur={() => syncAnswer(localAnswer)}
            placeholder="Type your answer here..."
            className="w-full min-h-[120px] bg-white border-2 border-[#E8E0F0] rounded-xl px-4 py-3 text-[15px] text-[#2D243D] placeholder:text-[#9B7FD4]/60 focus:outline-none focus:border-[#7A5BB5] focus:ring-4 focus:ring-[#7A5BB5]/5 transition-all shadow-inner"
          />
          <button
            type="button"
            disabled={isEvaluating || !localAnswer.trim()}
            onClick={() => {
              // Ensure store is updated before submitting
              syncAnswer(localAnswer)
              handleSubmitAnswer({ ...q, user_answer: localAnswer })
            }}
            className="inline-flex items-center justify-center px-6 py-2.5 rounded-xl bg-[#7A5BB5] text-white text-sm font-bold shadow-md hover:bg-[#6847a1] disabled:opacity-50 transition-all active:scale-95"
          >
            {isEvaluating ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin text-lg">⟳</span> Verifying...
              </span>
            ) : "Verify Answer"}
          </button>
        </div>
      ) : (
        <div className={`p-5 rounded-2xl border transition-all ${
          evaluation?.correct === "true" ? "bg-[#E9F7EF] border-[#2E7D57]/20" : 
          evaluation?.correct === "partial" ? "bg-[#FFF9F2] border-[#D97706]/20" : 
          "bg-[#FAEFF5] border-[#A0527A]/20"
        }`}>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-xl">
              {evaluation?.correct === "true" ? "✅" : evaluation?.correct === "partial" ? "◑" : "❌"}
            </span>
            <p className={`text-sm font-bold ${
              evaluation?.correct === "true" ? "text-[#1B5E20]" : 
              evaluation?.correct === "partial" ? "text-[#92400E]" : 
              "text-[#83214F]"
            }`}>
              {evaluation?.feedback}
            </p>
          </div>
          {evaluation?.misconception && (
            <div className="mb-3 p-3 bg-white/40 rounded-lg">
              <p className="text-[11px] uppercase font-bold text-[#7A5BB5] mb-1">Misconception</p>
              <p className="text-xs text-[#3D344D] font-medium leading-relaxed">{evaluation?.misconception}</p>
            </div>
          )}
          {evaluation?.correction && (
            <div className="mb-3 p-3 bg-white/40 rounded-lg">
              <p className="text-[11px] uppercase font-bold text-[#2E7D57] mb-1">Correction</p>
              <p className="text-xs text-[#3D344D] font-medium leading-relaxed">{evaluation?.correction}</p>
            </div>
          )}
          <div className="pt-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[#7A5BB5] bg-white/60 px-2 py-0.5 rounded-md font-bold uppercase tracking-wider">
                📍 Confirmed by: {sourceTitle(evaluation?.cited_source_index ?? 0)} {findTimestampForSource(evaluation?.cited_source_index ?? 0)}
              </span>
            </div>
            <button
              onClick={() => {
                const updatedData = { 
                  ...data,
                  tutor_output: data.tutor_output ? {
                    ...data.tutor_output,
                    knowledge_check: data.tutor_output.knowledge_check.map((item) =>
                      item.id === q.id ? { ...item, answered: false, evaluation: null } : item
                    )
                  } : data.tutor_output
                }
                setResults(updatedData)
              }}
              className="text-[10px] font-bold text-[#7A5BB5] hover:underline uppercase tracking-widest"
            >
              Retry
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
