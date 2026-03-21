import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { question, transcript, chat_mode } = body

    let context_string = ''
    if (chat_mode === 'strict') {
      context_string = `Answer this question using ONLY the transcript below. If the answer is not in the transcript, say exactly: This is not covered in the video.\nQuestion: ${question}\nTranscript: ${transcript}`
    } else {
      context_string = `Answer this question. Use the transcript as your primary source but you may draw on broader knowledge. When adding information not in the transcript, prefix with [Beyond the video:]\nQuestion: ${question}\nTranscript: ${transcript}`
    }

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://notion-clips-production.up.railway.app'
    
    // We send it to Railway's /extract but explicitly request quick mode with just summary
    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript: context_string,
        mode: "quick",
        sections: { summary: true, key_takeaways: false, topics: false, action_items: false },
        duration_minutes: 0
      })
    })

    if (!res.ok) {
      throw new Error(`Failed to extract insights. Status: ${res.status}`)
    }

    const data = await res.json()
    return NextResponse.json({ answer: data.insights?.summary || "Could not generate answer." })
  } catch (error: any) {
    console.error("Chat API error:", error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
