"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { Mode } from './types'
import { getSupabaseClient } from './supabaseClient'

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
  videoId: string | null
  setVideoId: (val: string | null) => void
  mode: Mode
  setMode: (mode: Mode) => void
  results: any | null
  setResults: (val: any) => void
  transcript: string | null
  setTranscript: (val: string | null) => void
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
  const [videoId, setVideoId] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('study')
  const [results, setResults] = useState<any | null>(null)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [processingTime, setProcessingTime] = useState<number | null>(null)
  const [transcriptFetchMs, setTranscriptFetchMs] = useState<number | null>(null)
  const [extractMs, setExtractMs] = useState<number | null>(null)
  const [extractCacheHit, setExtractCacheHit] = useState<boolean | null>(null)
  const [transcriptCacheHit, setTranscriptCacheHit] = useState<boolean | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const [wordCount, setWordCount] = useState<number | null>(null)

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
      window.history.replaceState({}, '', '/')
    } else {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/notion/status/${id}`)
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
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo }
    })
    if (error) throw error
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
    setVideoId(null)
    setResults(null)
    setTranscript(null)
    setProcessingTime(null)
    setTranscriptFetchMs(null)
    setExtractMs(null)
    setExtractCacheHit(null)
    setTranscriptCacheHit(null)
    setDuration(null)
    setWordCount(null)
  }

  return (
    <AppContext.Provider value={{
      sessionId, userId, userEmail, isAuthenticated: Boolean(userId),
      signInWithGoogle, signOutGoogle, getCurrentUserId,
      isConnected, setIsConnected, disconnectNotion,
      notionPageId, setNotionPageId,
      url, setUrl, videoId, setVideoId,
      mode, setMode, results, setResults,
      transcript, setTranscript, processingTime, setProcessingTime,
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
