"use client"

import { useRef, useState } from "react"
import { useAppStore } from "@/lib/store"
import { StudySessionMode } from "@/components/StudySessionMode"
import { QuestionsInput } from "@/components/app/QuestionsInput"
import { SmartWatch } from "@/components/SmartWatch"
import { Youtube, FileText, Link as LinkIcon, Brain, FileUp, X } from "lucide-react"

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
    sessionId,
  } = useAppStore()
  const [error, setError] = useState("")
  const [questionsOpen, setQuestionsOpen] = useState(false)
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
    <div className="min-w-0 space-y-6">
      <div>
        <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2 mb-4 block">Content source</label>

        <div className="grid grid-cols-2 gap-3">
          {[
            {
              key: "youtube",
              title: "YouTube",
              subtitle: "Video + Smart Watch",
              icon: <Youtube className="w-5 h-5 mb-2" />,
            },
            {
              key: "pdf",
              title: "PDF Upload",
              subtitle: "Lecture notes & textbooks",
              icon: <FileText className="w-5 h-5 mb-2" />,
            },
            {
              key: "article",
              title: "Article URL",
              subtitle: "Blogs, docs, news",
              icon: <LinkIcon className="w-5 h-5 mb-2" />,
            },
            {
              key: "study_session",
              title: "Study Session",
              subtitle: "Multi-source knowledge map",
              icon: <Brain className="w-5 h-5 mb-2" />,
            },
          ].map((tab) => {
            const isActive = sourceType === tab.key
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => {
                  setSourceType(tab.key as "youtube" | "pdf" | "article" | "study_session")
                  setError("")
                }}
                className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all duration-200 group ${
                  isActive
                    ? "bg-[#F5F2FD] border-[#7A5BB5] shadow-sm ring-1 ring-[#7A5BB5]/10"
                    : "bg-white border-[#E8E0F0] hover:border-[#7A5BB5]/50 hover:bg-[#F9F8FF]"
                }`}
              >
                <div className={`${isActive ? "text-[#7A5BB5]" : "text-[#7D748C]"}`}>
                  {tab.icon}
                </div>
                <div className={`font-bold text-[14px] tracking-tight leading-tight ${isActive ? "text-[#3D344D]" : "text-[#5D546C]"}`}>
                  {tab.title}
                </div>
                <div className={`text-[11px] mt-1 leading-tight font-medium ${isActive ? "text-[#7A5BB5]" : "text-[#9B7FD4]"}`}>
                  {tab.subtitle}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {sourceType === "study_session" && <StudySessionMode />}

      {sourceType === "youtube" && (
        <div className="space-y-4">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <Youtube className="h-5 w-5 text-red-500/80 group-focus-within:text-red-500 transition-colors" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => handleYoutubeChange(e.target.value)}
              placeholder="Paste YouTube URL here..."
              className="w-full bg-white border border-[#E8E0F0] rounded-xl pl-11 pr-4 py-3.5 text-[1.02rem] text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-[#CDBAEF] transition-all shadow-sm"
            />
          </div>
          <button
            onClick={() => handleYoutubeChange("https://www.youtube.com/watch?v=dQw4w9WgXcQ")}
            className="text-xs text-[#7A5BB5] hover:text-[#5B428A] transition-colors inline-block"
          >
            Try a sample video →
          </button>
          
          <div className="pt-2 border-t border-[#E8E0F0]">
            <SmartWatch videoUrl={url} sessionId={sessionId} />
          </div>
        </div>
      )}

      {sourceType === "pdf" && (
        <div className="space-y-3">
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
            className="w-full border-2 border-dashed border-[#9B7FD4] rounded-xl p-6 flex flex-col items-center justify-center text-center hover:bg-[#7A5BB5]/5 transition-colors group"
          >
            <FileUp className="w-8 h-8 text-[#9B7FD4] mb-3 group-hover:scale-110 transition-transform" />
            <div className="text-[1.02rem] font-medium text-foreground">Drop PDF here or click to browse</div>
            <div className="text-xs text-muted mt-1">(max 10MB)</div>
          </button>
          {pdfFile && (
            <div className="flex items-center justify-between gap-3 px-4 py-3 bg-[#F0EBF8] rounded-xl border border-[#D9C2E8]">
              <div className="min-w-0 flex items-center gap-3">
                <div className="p-2 bg-white rounded-lg shrink-0">
                  <FileText className="w-4 h-4 text-[#7A5BB5]" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-[#3D2466] truncate">{pdfFile.name}</div>
                  <div className="text-xs text-[#7A5BB5]">{(pdfFile.size / (1024 * 1024)).toFixed(2)} MB</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setPdfFile(null)}
                className="p-2 text-[#A0527A] hover:bg-[#A0527A]/10 rounded-lg transition-colors shrink-0"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {sourceType === "article" && (
        <div className="space-y-4">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <LinkIcon className="h-4 w-4 text-[#9B7FD4] group-focus-within:text-[#7A5BB5] transition-colors" />
            </div>
            <input
              type="text"
              value={articleUrl}
              onChange={(e) => handleArticleChange(e.target.value)}
              placeholder="Paste article, blog, or documentation URL..."
              className="w-full bg-white border border-[#E8E0F0] rounded-xl pl-10 pr-4 py-3.5 text-[1.02rem] text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-[#CDBAEF] transition-all shadow-sm"
            />
          </div>
        </div>
      )}

      {error && sourceType !== "study_session" && (
        <div className="text-sm text-[#A0527A] bg-[#FAEFF5] px-3 py-2 rounded-lg border border-[#E6C7D6]">{error}</div>
      )}

      {sourceType !== "study_session" && (
        <div className="pt-2">
          <button 
            className="flex items-center justify-between w-full text-sm font-medium text-[#7A5BB5] hover:text-[#5B428A] transition-colors"
            onClick={() => setQuestionsOpen(!questionsOpen)}
          >
            <span>Ask specific questions (optional)</span>
            <span className={`transform transition-transform ${questionsOpen ? "rotate-180" : ""}`}>▼</span>
          </button>
          {questionsOpen && (
            <div className="mt-3">
              <QuestionsInput questions={questions} onChange={setQuestions} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
