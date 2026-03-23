"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { Mode } from './types'

interface AppState {
  sessionId: string | null
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
  duration: number | null
  setDuration: (val: number | null) => void
  wordCount: number | null
  setWordCount: (val: number | null) => void
  reset: () => void
}

const AppContext = createContext<AppState | undefined>(undefined)

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [notionPageId, setNotionPageId] = useState<string | null>(null)
  const [url, setUrl] = useState("")
  const [videoId, setVideoId] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('study')
  const [results, setResults] = useState<any | null>(null)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [processingTime, setProcessingTime] = useState<number | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const [wordCount, setWordCount] = useState<number | null>(null)

  useEffect(() => {
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
  }, [])

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
    setDuration(null)
    setWordCount(null)
  }

  return (
    <AppContext.Provider value={{
      sessionId, isConnected, setIsConnected, disconnectNotion,
      notionPageId, setNotionPageId,
      url, setUrl, videoId, setVideoId,
      mode, setMode, results, setResults,
      transcript, setTranscript, processingTime, setProcessingTime,
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
