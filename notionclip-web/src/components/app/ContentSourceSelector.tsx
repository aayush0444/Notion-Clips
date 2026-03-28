"use client"

import { useRef, useState } from "react"
import { useAppStore } from "@/lib/store"
import { StudySessionMode } from "@/components/StudySessionMode"
import { QuestionsInput } from "@/components/app/QuestionsInput"

const MAX_PDF_BYTES = 10 * 1024 * 1024

function extractYoutubeId(text: string) {
  const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/
  const match = text.match(regExp)
  return match && match[2].length === 11 ? match[2] : null
}

function isLikelyYoutubeUrl(value: string) {
  const v = value.toLowerCase()
  return v.includes("youtube.com") || v.includes("youtu.be")
}

export function ContentSourceSelector() {
  const {
    sourceType,
    setSourceType,
    url,
    setUrl,
    setVideoId,
    videoId,
    setTranscript,
    setDuration,
    articleUrl,
    setArticleUrl,
    pdfFile,
    setPdfFile,
    questions,
    setQuestions,
  } = useAppStore()
  const [error, setError] = useState("")
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleYoutubeChange = (value: string) => {
    setUrl(value)
    setVideoId(extractYoutubeId(value))
    setTranscript(null)
    setDuration(null)
    setError("")
  }

  const handleArticleChange = (value: string) => {
    setArticleUrl(value)
    if (isLikelyYoutubeUrl(value)) {
      setError("Use YouTube tab for YouTube links.")
    } else {
      setError("")
    }
  }

  const handleFile = (file: File | null) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only .pdf files are supported.")
      return
    }
    if (file.size > MAX_PDF_BYTES) {
      setError("PDF must be under 10MB.")
      return
    }
    setError("")
    setPdfFile(file)
  }

  return (
    <div className="space-y-3">
      <label className="block text-xs text-white/40 uppercase tracking-wider">Content source</label>

      <div className="inline-flex rounded-lg border border-white/10 bg-white/[0.03] p-1">
        {[
          { key: "youtube", label: "YouTube" },
          { key: "pdf", label: "PDF Upload" },
          { key: "article", label: "Article URL" },
          { key: "study_session", label: "Study Session" },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => {
              setSourceType(tab.key as "youtube" | "pdf" | "article" | "study_session")
              setError("")
            }}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
              sourceType === tab.key
                ? "bg-white text-black"
                : "text-white/70 hover:bg-white/10"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {sourceType === "study_session" && <StudySessionMode />}

      {sourceType === "youtube" && (
        <div className="space-y-2">
          <input
            type="text"
            value={url}
            onChange={(e) => handleYoutubeChange(e.target.value)}
            placeholder="https://youtube.com/watch?v=..."
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-3 text-sm text-white/90 placeholder:text-white/30"
          />
          {videoId && <div className="text-xs text-green-400">Video ID: {videoId}</div>}
        </div>
      )}

      {sourceType === "pdf" && (
        <div className="space-y-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] || null)}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="w-full border border-dashed border-white/20 rounded-lg px-3 py-5 text-sm text-white/75 hover:bg-white/[0.04]"
          >
            Drag & drop PDF here or click to browse (max 10MB)
          </button>
          {pdfFile && (
            <div className="text-xs text-white/75 flex items-center justify-between">
              <span>{pdfFile.name} · {(pdfFile.size / (1024 * 1024)).toFixed(2)} MB</span>
              <button
                type="button"
                onClick={() => setPdfFile(null)}
                className="text-red-300 hover:text-red-200"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}

      {sourceType === "article" && (
        <input
          type="text"
          value={articleUrl}
          onChange={(e) => handleArticleChange(e.target.value)}
          placeholder="Paste any article, blog post, or documentation URL"
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-3 text-sm text-white/90 placeholder:text-white/30"
        />
      )}

      {error && sourceType !== "study_session" && <div className="text-xs text-red-300">{error}</div>}

      {sourceType !== "study_session" && (
        <QuestionsInput questions={questions} onChange={setQuestions} />
      )}
    </div>
  )
}

