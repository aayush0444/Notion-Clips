"use client"
import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { Send } from 'lucide-react'
import { api } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  notionEdited?: boolean
}

export function QnASection() {
  const { mode, transcript, notionPageId, sessionId } = useAppStore()
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

  const chatPlaceholderByMode = {
    study: "Ask for concept clarity, formula meaning, or exam-style explanation...",
    work: "Ask for recommendation, tradeoff, or implementation decision...",
    quick: "Ask for the fastest takeaway or a plain-language explanation...",
  } as const

  const chatLabelByMode = {
    study: "Ask Study Questions",
    work: "Ask Work Questions",
    quick: "Ask Quick Questions",
  } as const

  const handleSend = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    const historyBefore = [...messages]
    const newMessages = [...historyBefore, { role: 'user', content: trimmed } as Message]
    setMessages(newMessages)
    setInput("")
    setError("")

    try {
      let answer = await api.askChat(
        trimmed,
        transcript,
        mode,
        'strict',
        historyBefore,
        sessionId,
        notionPageId
      )
      const notionEdited = answer.startsWith("[NOTION_EDITED]")
      if (notionEdited) {
        answer = answer.replace("[NOTION_EDITED]", "").trim()
      }
      setMessages([...newMessages, { role: 'assistant', content: answer, notionEdited }])
    } catch (err: any) {
      setError(err?.message || "Couldn’t get a clean answer right now. Please try again.")
    }
  }

  return (
    <div className="border-t border-white/5 pt-6 mt-6">
      <div
        className="text-xs text-white/40 mb-3 uppercase tracking-wider"
        title={chatPlaceholderByMode[mode]}
      >
        {chatLabelByMode[mode]}
      </div>
      
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
              <span>{msg.content}</span>
              {msg.notionEdited && (
                <span className="ml-2 inline-flex items-center text-green-400 text-xs font-semibold">
                  ✓ Notion updated
                </span>
              )}
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
          placeholder={chatPlaceholderByMode[mode]}
          title={chatPlaceholderByMode[mode]}
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-white/20 focus:bg-white/[0.07] transition-colors"
        />
        <button
          onClick={() => handleSend(input)}
          disabled={!input.trim()}
          title="Send question"
          className="px-4 py-2.5 bg-white/10 hover:bg-white/15 disabled:opacity-40 disabled:cursor-not-allowed border border-white/10 rounded-lg transition-all"
        >
          <Send className="w-4 h-4 text-white/70" />
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-danger">{error}</p>}
    </div>
  )
}
