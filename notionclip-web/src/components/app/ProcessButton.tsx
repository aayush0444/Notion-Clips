"use client"
import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'

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
  const modeCta = {
    study: "Build Study Notes",
    work: "Build Work Brief",
    quick: "Generate Quick Summary",
  } as const
  const modeHint = {
    study: "Deep notes with formulas, key facts, and self-test prompts.",
    work: "Decision-focused brief with tools, decisions, and next actions.",
    quick: "Fast high-signal summary with key takeaways.",
  } as const
  const sourceHint = {
    youtube: "YouTube transcript extraction",
    pdf: "PDF text extraction",
    article: "Article content extraction",
    study_session: "Study Session workspace",
  } as const

  useEffect(() => {
    setError("")
  }, [url, articleUrl, pdfFile, sourceType])

  const canProcess =
    sourceType === 'study_session'
      ? false
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
        setTranscript(null)
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
        setTranscript(null)
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
      <Button 
        variant="default" 
        className="w-full bg-white text-black py-3.5 rounded-lg hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm font-medium h-auto"
        disabled={!canProcess || loading}
        onClick={handleProcess}
        title={modeHint[mode]}
      >
        {loading ? "Building your output..." : sourceType === 'youtube' ? 'Process Video' : modeCta[mode]}
      </Button>
      <p className="mt-2 text-xs text-white/45" title={modeHint[mode]}>
        {modeHint[mode]} · {sourceHint[sourceType]}
      </p>
      {error && (
        <p className="text-center text-sm text-danger mt-3">
          {error || "We hit a temporary issue. Please retry in a few seconds."}
        </p>
      )}
    </div>
  )
}
