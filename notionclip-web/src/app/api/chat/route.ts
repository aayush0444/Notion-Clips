import { NextResponse } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://notion-clips-production.up.railway.app'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const res = await fetch(`${API_BASE}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: body.question,
        transcript: body.transcript,
        mode: body.mode,
        chat_history: body.chat_history || [],
        notion_page_id: body.notion_page_id || null,
        session_id: body.session_id || null
      }),
    })

    if (!res.ok) {
      const errorBody = await res.text()
      throw new Error(`Backend error ${res.status}: ${errorBody}`)
    }

    const data = await res.json()
    return NextResponse.json({ answer: data.answer })
  } catch (error: any) {
    console.error('Chat route error:', error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
