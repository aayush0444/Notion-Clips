"use client"
import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Send } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function QnASection() {
  const { mode, transcript } = useAppStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [error, setError] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    console.log("Transcript length:", transcript?.length)
  }, [transcript])

  if (!transcript) return null

  const handleSend = async (text: string) => {
    if (!text.trim()) return
    const newMessages = [...messages, { role: 'user', content: text } as Message]
    setMessages(newMessages)
    setInput("")
    setError("")

    try {
      const history = newMessages.slice(-6).map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`).join('\n')
      const contextualQuestion = `You are a knowledgeable assistant who has fully watched and understood a YouTube video. 
You have complete context of everything discussed in the video — the topic, arguments made, 
people mentioned, events described, data cited, and conclusions drawn.

When a user asks something, first check if it relates to the video content directly or indirectly. 
Most questions — even ones that seem broad — are usually connected to what the video covered. 
Answer them generously using the video as your primary source, enriched with your own knowledge 
where it adds value.

Only if a question is completely unrelated to the video's subject matter — with zero connection 
to its topic, themes, or context — politely let the user know that the video does not cover that, 
and offer to answer from general knowledge if you can help.

Never be robotic or dismissive. Always try to be genuinely useful.

Transcript of the video:
${transcript}

Recent chat (last 6 messages):
${history}

User question: ${text}`
      const answer = await api.askChat(contextualQuestion, transcript, mode, 'strict', newMessages)
      setMessages([...newMessages, { role: 'assistant', content: answer }])
    } catch (err: any) {
      setError(err?.message || "Failed to get response.")
    }
  }

  return (
    <div className="border-t border-white/5 pt-6 mt-6">
      <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Ask Follow-up Questions</div>
      
      {messages.length > 0 && (
        <div className="mb-4 space-y-3 max-h-[200px] overflow-y-auto">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`text-sm ${
                msg.role === 'user'
                  ? 'text-white/90 bg-white/5 border border-white/10 rounded-lg px-3 py-2'
                  : 'text-white/70 pl-3 border-l-2 border-purple-500/30'
              }`}
            >
              {msg.content}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend(input)
            }
          }}
          placeholder="Ask about the video content..."
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-white/20 focus:bg-white/[0.07] transition-colors"
        />
        <button
          onClick={() => handleSend(input)}
          disabled={!input.trim()}
          className="px-4 py-2.5 bg-white/10 hover:bg-white/15 disabled:opacity-40 disabled:cursor-not-allowed border border-white/10 rounded-lg transition-all"
        >
          <Send className="w-4 h-4 text-white/70" />
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-danger">{error}</p>}
    </div>
  )
}
