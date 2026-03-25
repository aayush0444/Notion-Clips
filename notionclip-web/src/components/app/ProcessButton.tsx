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
    url, videoId, mode, setResults, setTranscript, setProcessingTime, setWordCount, setDuration,
    setTranscriptFetchMs, setExtractMs, setTranscriptCacheHit, setExtractCacheHit
  } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    setError("")
  }, [url])

  const handleProcess = async () => {
    if (!videoId) return
    setLoading(true)
    onProcessingChange?.(true)
    setResults(null)
    setError("")
    
    try {
      const start = Date.now()
      onStageChange?.('transcript')
      const transcriptStart = Date.now()
      const transcriptRes = await api.getTranscript(videoId)
      const transcriptTime = Date.now() - transcriptStart
      const { transcript, duration_minutes, cache_hit, fetch_ms } = transcriptRes
      setTranscript(transcript)
      setDuration(duration_minutes || null)
      setTranscriptCacheHit(typeof cache_hit === "boolean" ? cache_hit : null)
      setTranscriptFetchMs(typeof fetch_ms === "number" ? fetch_ms : transcriptTime)

      onStageChange?.('extract')
      const extractStart = Date.now()
      const extractRes = await api.extractInsights(transcript, mode)
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
      setError(err.message || "Failed to process video.")
      setLoading(false)
      onProcessingChange?.(false)
    }
  }

  return (
    <div className="w-full">
      <Button 
        variant="default" 
        className="w-full bg-white text-black py-3.5 rounded-lg hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm font-medium h-auto"
        disabled={!videoId || loading}
        onClick={handleProcess}
      >
        {loading ? "Processing..." : "Process Video"}
      </Button>
      {error && <p className="text-center text-sm text-danger mt-3">{error}</p>}
    </div>
  )
}
