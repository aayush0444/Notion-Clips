import { NextResponse } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://notion-clips-production.up.railway.app'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { question, transcript, chat_history } = body

    const historyText = (chat_history || [])
      .slice(-6)
      .map((m: { role: string; content: string }) =>
        `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`
      )
      .join('\n')

    const context = `You are a helpful assistant that answers questions about a YouTube video.
Use the transcript below as your primary source. If the answer is not in the transcript, say so briefly then answer from general knowledge if you can.
Be concise. Answer in 2-4 sentences unless more is genuinely needed.

${historyText ? `Conversation so far:\n${historyText}\n` : ''}
Question: ${question}

Transcript:
${transcript}`

    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript: context,
        mode: 'quick',
        sections: { summary: true, key_takeaways: false, topics: false, action_items: false },
        duration_minutes: 0,
      })
    })

    if (!res.ok) {
      const errorBody = await res.text()
      throw new Error(`Backend error ${res.status}: ${errorBody}`)
    }

    const data = await res.json()
    const answer = data?.insights?.summary || data?.answer || "I couldn't find an answer to that."
    return NextResponse.json({ answer })
  } catch (error: any) {
    console.error('Chat route error:', error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
