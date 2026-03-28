"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { Mode } from './types'
import { getSupabaseClient } from './supabaseClient'
import { backendUrl } from './backendUrl'

const APP_STATE_KEY = "notionclip_app_state_v1"

type PersistedAppState = {
  url: string
  sourceType: 'youtube' | 'pdf' | 'article' | 'study_session'
  articleUrl: string
  videoId: string | null
  mode: Mode
  results: any | null
  transcript: string | null
  questions: string[]
  processingTime: number | null
  transcriptFetchMs: number | null
  extractMs: number | null
  extractCacheHit: boolean | null
  transcriptCacheHit: boolean | null
  duration: number | null
  wordCount: number | null
}

interface AppState {
  sessionId: string | null
  userId: string | null
  userEmail: string | null
  isAuthenticated: boolean
  signInWithGoogle: () => Promise<void>
  signOutGoogle: () => Promise<void>
  getCurrentUserId: () => Promise<string | null>
  isConnected: boolean
  setIsConnected: (val: boolean) => void
  disconnectNotion: () => void
  notionPageId: string | null
  setNotionPageId: (val: string | null) => void
  url: string
  setUrl: (val: string) => void
  sourceType: 'youtube' | 'pdf' | 'article' | 'study_session'
  setSourceType: (val: 'youtube' | 'pdf' | 'article' | 'study_session') => void
  articleUrl: string
  setArticleUrl: (val: string) => void
  pdfFile: File | null
  setPdfFile: (val: File | null) => void
  videoId: string | null
  setVideoId: (val: string | null) => void
  mode: Mode
  setMode: (mode: Mode) => void
  results: any | null
  setResults: (val: any) => void
  transcript: string | null
  setTranscript: (val: string | null) => void
  questions: string[]
  setQuestions: (val: string[]) => void
  processingTime: number | null
  setProcessingTime: (val: number | null) => void
  transcriptFetchMs: number | null
  setTranscriptFetchMs: (val: number | null) => void
  extractMs: number | null
  setExtractMs: (val: number | null) => void
  extractCacheHit: boolean | null
  setExtractCacheHit: (val: boolean | null) => void
  transcriptCacheHit: boolean | null
  setTranscriptCacheHit: (val: boolean | null) => void
  duration: number | null
  setDuration: (val: number | null) => void
  wordCount: number | null
  setWordCount: (val: number | null) => void
  reset: () => void
}

const AppContext = createContext<AppState | undefined>(undefined)

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [userId, setUserId] = useState<string | null>(null)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [notionPageId, setNotionPageId] = useState<string | null>(null)
  const [url, setUrl] = useState("")
  const [sourceType, setSourceType] = useState<'youtube' | 'pdf' | 'article' | 'study_session'>('youtube')
  const [articleUrl, setArticleUrl] = useState("")
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [videoId, setVideoId] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('study')
  const [results, setResults] = useState<any | null>(null)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [questions, setQuestions] = useState<string[]>([])
  const [processingTime, setProcessingTime] = useState<number | null>(null)
  const [transcriptFetchMs, setTranscriptFetchMs] = useState<number | null>(null)
  const [extractMs, setExtractMs] = useState<number | null>(null)
  const [extractCacheHit, setExtractCacheHit] = useState<boolean | null>(null)
  const [transcriptCacheHit, setTranscriptCacheHit] = useState<boolean | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const [wordCount, setWordCount] = useState<number | null>(null)

  useEffect(() => {
    if (typeof window === "undefined") return
    try {
      const raw = window.localStorage.getItem(APP_STATE_KEY)
      if (!raw) return
      const saved = JSON.parse(raw) as PersistedAppState
      if (typeof saved.url === "string") setUrl(saved.url)
      if (saved.sourceType) setSourceType(saved.sourceType)
      if (typeof saved.articleUrl === "string") setArticleUrl(saved.articleUrl)
      if (typeof saved.videoId === "string" || saved.videoId === null) setVideoId(saved.videoId)
      if (saved.mode) setMode(saved.mode)
      if (saved.results !== undefined) setResults(saved.results)
      if (typeof saved.transcript === "string" || saved.transcript === null) setTranscript(saved.transcript)
      if (Array.isArray(saved.questions)) setQuestions(saved.questions)
      if (typeof saved.processingTime === "number" || saved.processingTime === null) setProcessingTime(saved.processingTime)
      if (typeof saved.transcriptFetchMs === "number" || saved.transcriptFetchMs === null) setTranscriptFetchMs(saved.transcriptFetchMs)
      if (typeof saved.extractMs === "number" || saved.extractMs === null) setExtractMs(saved.extractMs)
      if (typeof saved.extractCacheHit === "boolean" || saved.extractCacheHit === null) setExtractCacheHit(saved.extractCacheHit)
      if (typeof saved.transcriptCacheHit === "boolean" || saved.transcriptCacheHit === null) setTranscriptCacheHit(saved.transcriptCacheHit)
      if (typeof saved.duration === "number" || saved.duration === null) setDuration(saved.duration)
      if (typeof saved.wordCount === "number" || saved.wordCount === null) setWordCount(saved.wordCount)
    } catch {
      // Ignore persisted state parse errors.
    }
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return
    const payload: PersistedAppState = {
      url,
      sourceType,
      articleUrl,
      videoId,
      mode,
      results,
      transcript,
      questions,
      processingTime,
      transcriptFetchMs,
      extractMs,
      extractCacheHit,
      transcriptCacheHit,
      duration,
      wordCount,
    }
    try {
      window.localStorage.setItem(APP_STATE_KEY, JSON.stringify(payload))
    } catch {
      // Ignore storage failures.
    }
  }, [
    url,
    sourceType,
    articleUrl,
    videoId,
    mode,
    results,
    transcript,
    questions,
    processingTime,
    transcriptFetchMs,
    extractMs,
    extractCacheHit,
    transcriptCacheHit,
    duration,
    wordCount,
  ])

  useEffect(() => {
    const supabase = getSupabaseClient()
    const syncUser = async () => {
      const { data } = await supabase.auth.getSession()
      const user = data.session?.user
      setUserId(user?.id || null)
      setUserEmail(user?.email || null)
    }
    syncUser()

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
      const user = session?.user
      setUserId(user?.id || null)
      setUserEmail(user?.email || null)
    })

    let id = localStorage.getItem("notionclip_session_id")
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem("notionclip_session_id", id)
    }
    setSessionId(id)

    const params = new URLSearchParams(window.location.search)
    if (params.get("connected") === "true") {
      setIsConnected(true)
      const cleanPath = window.location.pathname || '/app'
      window.history.replaceState({}, '', cleanPath)
    } else {
      fetch(backendUrl(`/auth/notion/status/${id}`))
        .then(res => res.json())
        .then(data => {
          if (data.has_token) setIsConnected(true)
        })
        .catch(() => {})
    }

    return () => {
      authListener.subscription.unsubscribe()
    }
  }, [])

  const signInWithGoogle = async () => {
    const supabase = getSupabaseClient()
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/app` : undefined
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo,
        skipBrowserRedirect: true,
      }
    })
    if (error) throw error
    if (data?.url && typeof window !== "undefined") {
      window.location.assign(data.url)
    }
  }

  const signOutGoogle = async () => {
    const supabase = getSupabaseClient()
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  const getCurrentUserId = async (): Promise<string | null> => {
    const supabase = getSupabaseClient()
    const { data } = await supabase.auth.getSession()
    const liveUserId = data.session?.user?.id || null
    if (liveUserId && liveUserId !== userId) {
      setUserId(liveUserId)
      setUserEmail(data.session?.user?.email || null)
    }
    return liveUserId
  }

  const disconnectNotion = () => {
    setIsConnected(false)
    if (sessionId) {
      localStorage.removeItem("notionclip_session_id")
    }
    const newId = crypto.randomUUID()
    localStorage.setItem("notionclip_session_id", newId)
    setSessionId(newId)
  }

  const reset = () => {
    setUrl("")
    setArticleUrl("")
    setPdfFile(null)
    setSourceType("youtube")
    setVideoId(null)
    setResults(null)
    setTranscript(null)
    setQuestions([])
    setProcessingTime(null)
    setTranscriptFetchMs(null)
    setExtractMs(null)
    setExtractCacheHit(null)
    setTranscriptCacheHit(null)
    setDuration(null)
    setWordCount(null)
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(APP_STATE_KEY)
    }
  }

  return (
    <AppContext.Provider value={{
      sessionId, userId, userEmail, isAuthenticated: Boolean(userId),
      signInWithGoogle, signOutGoogle, getCurrentUserId,
      isConnected, setIsConnected, disconnectNotion,
      notionPageId, setNotionPageId,
      url, setUrl,
      sourceType, setSourceType, articleUrl, setArticleUrl, pdfFile, setPdfFile,
      videoId, setVideoId,
      mode, setMode, results, setResults,
      transcript, setTranscript, questions, setQuestions, processingTime, setProcessingTime,
      transcriptFetchMs, setTranscriptFetchMs, extractMs, setExtractMs,
      extractCacheHit, setExtractCacheHit,
      transcriptCacheHit, setTranscriptCacheHit,
      duration, setDuration,
      wordCount, setWordCount, reset
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppStore() {
  const context = useContext(AppContext)
  if (!context) throw new Error("useAppStore must be used within AppProvider")
  return context
}
