"use client"
import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'
import { motion } from 'framer-motion'

type ProcessButtonProps = {
  onProcessingChange?: (loading: boolean) => void
  onStageChange?: (stage: 'transcript' | 'extract' | 'finalizing') => void
}

export function ProcessButton({ onProcessingChange, onStageChange }: ProcessButtonProps) {
  const {
    sourceType, url, articleUrl, pdfFile, videoId, mode, sessionId, userId, questions, transcript, setResults, setTranscript, setProcessingTime, setWordCount, setDuration,
    setTranscriptFetchMs, setExtractMs, setTranscriptCacheHit, setExtractCacheHit
  } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  // Determine button text dynamically based on sourceType and mode
  let buttonLabel = ""
  if (sourceType === "youtube") {
    if (mode === "study") buttonLabel = "Extract Study Notes →"
    else if (mode === "work") buttonLabel = "Generate Work Brief →"
    else if (mode === "quick") buttonLabel = "Quick Summary →"
    else buttonLabel = "Process Video →"
  } else if (sourceType === "pdf") {
    if (mode === "study") buttonLabel = "Extract from PDF →"
    else if (mode === "work") buttonLabel = "Brief PDF Content →"
    else buttonLabel = "Summarize PDF →"
  } else if (sourceType === "article") {
    if (mode === "work") buttonLabel = "Brief This Article →"
    else if (mode === "study") buttonLabel = "Study This Article →"
    else buttonLabel = "Summarize Article →"
  } else if (sourceType === "study_session") {
    buttonLabel = "Start Learning Session 🧠"
  }

  useEffect(() => {
    setError("")
  }, [url, articleUrl, pdfFile, sourceType])

  const canProcess =
    sourceType === 'study_session'
      ? false // Handled in StudySessionMode component? Wait, user asked to style it the same... actually Study Session has its own button, but let's keep it disabled if it is here. Wait, study session button is handled there.
      : sourceType === 'youtube'
      ? Boolean(videoId)
      : sourceType === 'pdf'
      ? Boolean(pdfFile)
      : Boolean(articleUrl && articleUrl.startsWith('http'))

  const handleProcess = async () => {
    if (!canProcess) return
    setLoading(true)
    onProcessingChange?.(true)
    setResults(null)
    setError("")
    
    try {
      const start = Date.now()
      onStageChange?.('transcript')
      let contentText = ""
      if (sourceType === 'youtube') {
        if (transcript && transcript.trim().length > 0) {
          contentText = transcript
          setTranscriptFetchMs(0)
        } else {
          const transcriptStart = Date.now()
          const transcriptRes = await api.getTranscript(videoId as string)
          const transcriptTime = Date.now() - transcriptStart
          const { transcript, duration_minutes, cache_hit, fetch_ms } = transcriptRes
          contentText = transcript
          setTranscript(transcript)
          setDuration(duration_minutes || null)
          setTranscriptCacheHit(typeof cache_hit === "boolean" ? cache_hit : null)
          setTranscriptFetchMs(typeof fetch_ms === "number" ? fetch_ms : transcriptTime)
        }
      } else if (sourceType === 'pdf') {
        const readStart = Date.now()
        onStageChange?.('extract')
        const extractRes = await api.extractPdfInsights(pdfFile as File, mode, sessionId, userId)
        setTranscript(extractRes.source_text || null)
        setDuration(null)
        setTranscriptCacheHit(null)
        setTranscriptFetchMs(Date.now() - readStart)
        const extractTime = Date.now() - readStart
        setExtractMs(extractTime)
        setExtractCacheHit(typeof extractRes.cache_hit === "boolean" ? extractRes.cache_hit : null)
        const totalTime = Date.now() - start
        setProcessingTime(totalTime)
        setWordCount(extractRes.word_count || 0)
        onStageChange?.('finalizing')
        setTimeout(() => {
          setResults(extractRes.insights)
          setLoading(false)
          onProcessingChange?.(false)
        }, 500)
        return
      } else {
        const readStart = Date.now()
        onStageChange?.('extract')
        const extractRes = await api.extractArticleInsights(articleUrl, mode, sessionId, userId)
        setTranscript(extractRes.source_text || null)
        setDuration(null)
        setTranscriptCacheHit(null)
        setTranscriptFetchMs(Date.now() - readStart)
        const extractTime = Date.now() - readStart
        setExtractMs(extractTime)
        setExtractCacheHit(typeof extractRes.cache_hit === "boolean" ? extractRes.cache_hit : null)
        const totalTime = Date.now() - start
        setProcessingTime(totalTime)
        setWordCount(extractRes.word_count || 0)
        onStageChange?.('finalizing')
        setTimeout(() => {
          setResults(extractRes.insights)
          setLoading(false)
          onProcessingChange?.(false)
        }, 500)
        return
      }

      onStageChange?.('extract')
      const extractStart = Date.now()
      const extractRes = await api.extractInsights(contentText, mode, questions)
      const extractTime = Date.now() - extractStart
      setExtractMs(extractTime)
      setExtractCacheHit(typeof extractRes.cache_hit === "boolean" ? extractRes.cache_hit : null)
      if (typeof extractRes.duration_minutes === "number" && extractRes.duration_minutes > 0) {
        setDuration(extractRes.duration_minutes)
      }
      
      const totalTime = Date.now() - start
      setProcessingTime(totalTime)
      setWordCount(extractRes.word_count || 0)

      onStageChange?.('finalizing')
      setTimeout(() => {
        setResults(extractRes.insights)
        setLoading(false)
        onProcessingChange?.(false)
      }, 500)
    } catch (err: any) {
      console.error(err)
      setError(err.message || "Failed to process content.")
      setLoading(false)
      onProcessingChange?.(false)
    }
  }

  return (
    <div className="w-full">
      <motion.button 
        whileHover={{ scale: canProcess && !loading ? 1.02 : 1 }}
        whileTap={{ scale: canProcess && !loading ? 0.98 : 1 }}
        className="w-full h-12 rounded-xl bg-[#7A5BB5] flex items-center justify-center text-white font-bold text-[16px] transition-all disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!canProcess || loading}
        onClick={handleProcess}
      >
        {loading ? "Building your output..." : buttonLabel}
      </motion.button>
      {error && (
        <p className="text-center text-sm text-[#A0527A] mt-3 bg-[#FAEFF5] px-3 py-2 rounded-lg border border-[#E6C7D6]">
          {error || "We hit a temporary issue. Please retry in a few seconds."}
        </p>
      )}
    </div>
  )
}
