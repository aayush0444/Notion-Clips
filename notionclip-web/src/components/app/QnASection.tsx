"use client"
import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { Loader2, Send } from 'lucide-react'
import { api } from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  role: 'user' | 'assistant'
  content: string
  notionEdited?: boolean
}

export function QnASection() {
  const { 
    mode, 
    sourceType,
    results,
    transcript, 
    notionPageId, 
    sessionId, 
    userId,
    chatHistory: messages, 
    setChatHistory: setMessages 
  } = useAppStore()
  const [input, setInput] = useState("")
  const [error, setError] = useState("")
  const [isAsking, setIsAsking] = useState(false)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }, [messages, isAsking])

  useEffect(() => {
    console.log("Transcript length:", transcript?.length)
  }, [transcript])

  if (!transcript && sourceType !== "study_session") return null
  if (sourceType === "study_session" && !results) return null

  const chatPlaceholderByMode = {
    study: "Ask for concept clarity, formula meaning, or exam-style explanation...",
    work: "Ask for recommendation, tradeoff, or implementation decision...",
    quick: "Ask for the fastest takeaway or a plain-language explanation...",
    study_session: "Ask about your study session sources, contradictions, or concepts...",
  } as const

  const chatLabelByMode = {
    study: "Ask Study Questions",
    work: "Ask Work Questions",
    quick: "Ask Quick Questions",
    study_session: "Ask Study Session",
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
      let answer = ""
      if (sourceType === "study_session" && results?.study_session_id) {
        answer = await api.askStudySessionChat(
          results.study_session_id,
          trimmed,
          historyBefore,
          sessionId || "",
          userId
        )
      } else if (transcript) {
        answer = await api.askChat(
          trimmed,
          transcript,
          mode,
          'strict',
          historyBefore,
          sessionId,
          notionPageId
        )
      }
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
    <div className="h-full flex flex-col pt-2">
      <div
        className="text-xs app-text-muted mb-3 uppercase tracking-wider shrink-0"
        title={chatPlaceholderByMode[mode]}
      >
        {chatLabelByMode[mode]}
      </div>
      
      <div ref={scrollContainerRef} className="flex-1 min-h-0 overflow-y-auto mb-4 space-y-4 pr-2 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
        {messages.length > 0 && (
          <>
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`text-sm ${
                msg.role === 'user'
                  ? 'text-slate-900 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 shadow-sm'
                  : 'text-slate-900 pl-4 border-l-2 border-[#6F52A8] space-y-2'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none prose-headings:text-slate-900 prose-headings:font-bold prose-p:text-slate-900 prose-p:leading-relaxed prose-li:text-slate-900 marker:text-slate-900 prose-strong:text-black prose-p:my-1.5 prose-headings:my-3 prose-ul:list-disc prose-ul:ml-5 prose-ol:list-decimal prose-ol:ml-5 prose-table:border prose-table:border-collapse prose-td:border prose-td:p-2 prose-th:border prose-th:p-2">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <span>{msg.content}</span>
              )}
              {msg.notionEdited && (
                <div className="mt-2 inline-flex items-center text-[#5A8A63] text-xs font-semibold bg-[#E8F5E9] px-2 py-0.5 rounded">
                  ✓ Notion updated
                </div>
              )}
            </div>
          ))}
          {isAsking && (
            <div className="text-slate-600 pl-4 border-l-2 border-[#CCB8EE]">
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
          </>
        )}
      </div>

      <div className="flex gap-2 shrink-0">
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
