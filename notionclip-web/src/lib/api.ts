import {
  Mode,
  ExtractResponse,
  TranscriptResponse,
  VerdictResponse,
  SmartWatchDeepResult,
  SmartWatchQuickResult,
  SmartWatchHistoryResponse,
  SmartWatchDashboardResponse,
  CreateSessionResponse,
  StudySession,
  AnswerEvaluationResponse,
  ExportMarkdownResponse,
  SynthesisResponse
} from './types'
import { API_BASE, backendUrl } from './backendUrl'

async function parseError(res: Response): Promise<string> {
  let detail = `HTTP ${res.status}`
  try {
    const text = await res.text()
    if (text) {
      try {
        const parsed = JSON.parse(text)
        detail = parsed?.detail || parsed?.error || parsed?.message || text
      } catch {
        detail = text
      }
    }
  } catch {
    // keep default detail
  }
  return detail
}

export async function exportMarkdown(
  sessionId: string,
  sourceUrl: string = ""
): Promise<ExportMarkdownResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    source_url: sourceUrl,
  })
  const res = await fetch(
    `${backendUrl('/export/markdown')}?${params}`,
    { method: "GET" }
  )
  if (!res.ok) {
    throw new Error("Export failed")
  }
  return res.json()
}

export async function smartWatchQuickCheck(
  videoUrl: string,
  userQuestion: string,
  sessionId: string,
  transcript?: string | null
): Promise<SmartWatchQuickResult> {
  const res = await fetch(backendUrl('/smart-watch/quick-check'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_url: videoUrl,
      user_question: userQuestion,
      session_id: sessionId,
      transcript: transcript || null,
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Smart Watch quick check failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function smartWatchDeepAnalysis(
  videoId: string,
  userQuestion: string,
  sessionId: string,
  verdict: string
): Promise<SmartWatchDeepResult> {
  const res = await fetch(backendUrl('/smart-watch/deep-analysis'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: videoId,
      user_question: userQuestion,
      session_id: sessionId,
      verdict
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Smart Watch deep analysis failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function smartWatchHistory(
  sessionId: string,
  userId?: string | null,
  limit: number = 20
): Promise<SmartWatchHistoryResponse> {
  const res = await fetch(backendUrl('/smart-watch/history'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId || null,
      limit
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Smart Watch history failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function smartWatchAnalytics(
  sessionId: string,
  eventName: string,
  userId?: string | null,
  payload?: Record<string, unknown>
): Promise<void> {
  await fetch(backendUrl('/smart-watch/analytics'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      event_name: eventName,
      user_id: userId || null,
      payload: payload || {}
    })
  })
}

export async function smartWatchDashboard(
  sessionId: string,
  userId?: string | null
): Promise<SmartWatchDashboardResponse> {
  const res = await fetch(backendUrl('/smart-watch/dashboard'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId || null
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Smart Watch dashboard failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function createStudySession(
  learningGoal: string,
  studentLevel: string,
  sources: Array<{ type: string; url: string }>,
  sessionId: string,
  userId?: string
): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/study-session/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      learning_goal: learningGoal,
      student_level: studentLevel,
      sources,
      session_id: sessionId,
      user_id: userId || null
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Create study session failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function addPdfToSession(
  studySessionId: string,
  file: File
): Promise<{ source_index: number; title: string; status: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/study-session/${studySessionId}/add-pdf`, {
    method: 'POST',
    body: form
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Add PDF failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function buildStudySession(
  studySessionId: string,
  sessionId: string,
  userId?: string
): Promise<StudySession> {
  const res = await fetch(`${API_BASE}/study-session/${studySessionId}/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId || null
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Build session failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function getStudySession(
  studySessionId: string
): Promise<StudySession> {
  const res = await fetch(`${API_BASE}/study-session/${studySessionId}`)
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Fetch session failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function submitAnswer(
  studySessionId: string,
  questionId: string,
  userAnswer: string,
  sessionId: string,
  userId?: string
): Promise<AnswerEvaluationResponse> {
  const res = await fetch(`${API_BASE}/study-session/${studySessionId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: questionId,
      user_answer: userAnswer,
      session_id: sessionId,
      user_id: userId || null
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Submit answer failed (${res.status}): ${detail}`)
  }
  return res.json()
}

export async function pushStudySessionToNotion(
  studySessionId: string,
  sessionId: string,
  userId?: string
): Promise<{ status: string; notion_url: string }> {
  const res = await fetch(`${API_BASE}/study-session/${studySessionId}/push-notion`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId || null
    })
  })
  if (!res.ok) {
    const detail = await parseError(res)
    throw new Error(`Push to Notion failed (${res.status}): ${detail}`)
  }
  return res.json()
}

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

  async extractInsights(transcript: string, mode: Mode, questions?: string[]): Promise<ExtractResponse> {
    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript,
        mode,
        questions: questions && questions.length > 0 ? questions : undefined,
        sections: {}
      })
    })
    if (!res.ok) throw new Error("Failed to extract insights")
    return res.json()
  },

  async extractPdfInsights(file: File, mode: Mode, sessionId?: string | null, userId?: string | null): Promise<ExtractResponse> {
    const form = new FormData()
    form.append('file', file)
    form.append('mode', mode)
    form.append('session_id', sessionId || '')
    if (userId) form.append('user_id', userId)
    form.append('sections', JSON.stringify({}))
    const res = await fetch(`${API_BASE}/extract/pdf`, {
      method: 'POST',
      body: form
    })
    if (!res.ok) {
      const detail = await parseError(res)
      throw new Error(`PDF extraction failed (${res.status}): ${detail}`)
    }
    return res.json()
  },

  async extractArticleInsights(url: string, mode: Mode, sessionId?: string | null, userId?: string | null): Promise<ExtractResponse> {
    const res = await fetch(`${API_BASE}/extract/article`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        mode,
        session_id: sessionId || '',
        user_id: userId || null,
        sections: {}
      })
    })
    if (!res.ok) {
      const detail = await parseError(res)
      throw new Error(`Article extraction failed (${res.status}): ${detail}`)
    }
    return res.json()
  },

  async getPreWatchVerdict(transcript: string, mode: Mode): Promise<VerdictResponse> {
    const res = await fetch(`${API_BASE}/verdict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript, mode })
    })
    if (!res.ok) {
      let detail = `HTTP ${res.status}`
      try {
        const text = await res.text()
        if (text) {
          try {
            const parsed = JSON.parse(text)
            detail = parsed?.detail || parsed?.error || text
          } catch {
            detail = text
          }
        }
      } catch {
        // ignore parse failures
      }
      throw new Error(`Failed to generate verdict (${res.status}): ${detail}`)
    }
    return res.json()
  },

  smartWatchQuickCheck,
  smartWatchDeepAnalysis,
  smartWatchHistory,
  smartWatchAnalytics,
  smartWatchDashboard,

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

  async askChat(
    question: string,
    transcript: string,
    mode: string,
    chatMode: 'strict' | 'open',
    history: any[],
    sessionId?: string | null,
    notionPageId?: string | null
  ): Promise<string> {
    const safeHistory = (history || []).map((msg: any) => ({
      role: msg?.role === 'assistant' ? 'assistant' : 'user',
      content: String(msg?.content || '')
    }))

    const res = await fetch(`${API_BASE}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        transcript,
        mode,
        chat_mode: chatMode,
        chat_history: safeHistory,
        session_id: sessionId || null,
        notion_page_id: notionPageId || null
      })
    })
    if (!res.ok) {
      let detail = `HTTP ${res.status}`
      try {
        const raw = await res.text()
        if (raw) {
          try {
            const parsed = JSON.parse(raw)
            detail = parsed?.detail || parsed?.error || raw
          } catch {
            detail = raw
          }
        }
      } catch {
        // keep default detail
      }
      throw new Error(`Chat failed (${res.status}): ${detail}`)
    }
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
  },

  async synthesiseSessions(
    sessionIds: string[],
    userQuestion?: string
  ): Promise<SynthesisResponse> {
    const res = await fetch(`${API_BASE}/synthesis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_ids: sessionIds,
        user_question: userQuestion || null
      })
    })
    if (!res.ok) {
      const detail = await parseError(res)
      throw new Error(`Synthesis failed (${res.status}): ${detail}`)
    }
    return res.json()

  }
}
