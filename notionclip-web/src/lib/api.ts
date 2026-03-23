import { Mode, ExtractResponse, TranscriptResponse } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://notion-clips-production.up.railway.app'

export const api = {
  async getTranscript(videoId: string): Promise<TranscriptResponse> {
    const res = await fetch(`${API_BASE}/transcript`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id: videoId })
    })
    if (!res.ok) throw new Error("Failed to fetch transcript")
    return res.json()
  },

  async extractInsights(transcript: string, mode: Mode): Promise<ExtractResponse> {
    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript,
        mode,
        sections: {}
      })
    })
    if (!res.ok) throw new Error("Failed to extract insights")
    return res.json()
  },

  async pushToNotion(mode: string, insights: any, videoUrl: string, sessionId: string): Promise<{ status: string; page_id: string | null }> {
    const res = await fetch(`${API_BASE}/push`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, insights, video_url: videoUrl, session_id: sessionId })
    })
    if (!res.ok) throw new Error("Failed to push to Notion")
    const data = await res.json()
    return { status: data.status, page_id: data.page_id || null }
  },

  async askChat(question: string, transcript: string, mode: string, chatMode: 'strict' | 'open', history: any[]): Promise<string> {
    const res = await fetch(`/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, transcript, mode, chat_mode: chatMode, chat_history: history })
    })
    if (!res.ok) throw new Error("Failed to get chat response")
    const data = await res.json()
    return data.answer
  },

  async editNotion(page_id: string, instruction: string, session_id: string) {
    const res = await fetch(`${API_BASE}/notion/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page_id, instruction, session_id })
    })
    const data = await res.json()
    return data
  }
}
