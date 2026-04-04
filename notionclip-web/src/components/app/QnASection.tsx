"use client"
import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { Loader2, Send } from 'lucide-react'
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
  const [isAsking, setIsAsking] = useState(false)
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
    setIsAsking(true)

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
    } finally {
      setIsAsking(false)
    }
  }

  return (
    <div className="border-t border-border/70 pt-6 mt-6">
      <div
        className="text-xs app-text-muted mb-3 uppercase tracking-wider"
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
                  ? 'text-foreground bg-card border border-border rounded-lg px-3 py-2'
                  : 'text-foreground/75 pl-3 border-l-2 border-[#CDBAEF]'
              }`}
            >
              <span>{msg.content}</span>
              {msg.notionEdited && (
                <span className="ml-2 inline-flex items-center text-[#5A8A63] text-xs font-semibold">
                  ✓ Notion updated
                </span>
              )}
            </div>
          ))}
          {isAsking && (
            <div className="text-foreground/75 pl-3 border-l-2 border-[#CDBAEF]">
              <span className="inline-flex items-center gap-2 text-sm font-medium">
                <span className="h-4 w-4 rounded-full border-2 border-[#CCB8EE] border-t-[#6F52A8] animate-spin" />
                <span className="text-[#5E4A85]">Thinking</span>
                <span className="inline-flex items-center gap-1" aria-hidden="true">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#6F52A8] animate-pulse" />
                  <span className="h-1.5 w-1.5 rounded-full bg-[#6F52A8] animate-pulse [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-[#6F52A8] animate-pulse [animation-delay:240ms]" />
                </span>
              </span>
            </div>
          )}
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
          className="flex-1 bg-card border border-border rounded-lg px-4 py-2.5 text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-border-hover focus:bg-[#FCFAF7] transition-colors"
        />
        <button
          onClick={() => handleSend(input)}
          disabled={!input.trim() || isAsking}
          title="Send question"
          className="px-4 py-2.5 bg-[#F0EBF8] hover:bg-[#E4D9F5] disabled:opacity-40 disabled:cursor-not-allowed border border-border rounded-lg transition-all"
        >
          {isAsking ? (
            <Loader2 className="w-4 h-4 text-[#5A4A72] animate-spin" />
          ) : (
            <Send className="w-4 h-4 text-[#5A4A72]" />
          )}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-[#A0527A]">{error}</p>}
    </div>
  )
}
