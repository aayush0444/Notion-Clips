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
      <label className="block text-xs app-text-muted uppercase tracking-wider">Content source</label>

      <div className="inline-flex rounded-lg border border-border bg-card/80 p-1">
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
                ? "bg-[#7A5BB5] text-white"
                : "text-foreground/70 hover:bg-[#F0EBF8]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {sourceType === "study_session" && <StudySessionMode />}

      {sourceType === "youtube" && (
        <div className="space-y-2">
          <div className="tech-gradient-ring">
            <input
              type="text"
              value={url}
              onChange={(e) => handleYoutubeChange(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              className="bg-card px-3 py-3 text-sm text-foreground placeholder:text-muted"
            />
          </div>
          {videoId && <div className="text-xs text-[#5A8A63]">Video ID: {videoId}</div>}
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
            className="w-full border border-dashed border-border-hover rounded-lg px-3 py-5 text-sm text-foreground/75 hover:bg-[#F5F0E8]"
          >
            Drag & drop PDF here or click to browse (max 10MB)
          </button>
          {pdfFile && (
            <div className="text-xs text-foreground/75 flex items-center justify-between">
              <span>{pdfFile.name} · {(pdfFile.size / (1024 * 1024)).toFixed(2)} MB</span>
              <button
                type="button"
                onClick={() => setPdfFile(null)}
                className="text-[#A0527A] hover:opacity-80"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}

      {sourceType === "article" && (
        <div className="tech-gradient-ring">
          <input
            type="text"
            value={articleUrl}
            onChange={(e) => handleArticleChange(e.target.value)}
            placeholder="Paste any article, blog post, or documentation URL"
            className="bg-card px-3 py-3 text-sm text-foreground placeholder:text-muted"
          />
        </div>
      )}

      {error && sourceType !== "study_session" && <div className="text-xs text-[#A0527A]">{error}</div>}

      {sourceType !== "study_session" && (
        <QuestionsInput questions={questions} onChange={setQuestions} />
      )}
    </div>
  )
}

