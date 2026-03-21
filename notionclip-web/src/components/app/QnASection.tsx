"use client"
import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import { Send, Trash } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function QnASection() {
  const { mode, transcript } = useAppStore()
  const [chatMode, setChatMode] = useState<'strict'|'open'>('strict')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  if (!transcript) return null

  const getStaterChips = () => {
    if (mode === 'study') return ["Explain the core concept simply", "Give me three harder exam questions", "What formula should I focus on?"]
    if (mode === 'work') return ["What did they recommend and why?", "What should my team act on?", "Summarize the conclusion"]
    return ["What was the most surprising point?", "Give me the one-sentence version"]
  }

  const handleSend = async (text: string) => {
    if (!text.trim() || loading) return
    const newMessages = [...messages, { role: 'user', content: text } as Message]
    setMessages(newMessages)
    setInput("")
    setLoading(true)

    try {
      const answer = await api.askChat(text, transcript, mode, chatMode, newMessages)
      setMessages([...newMessages, { role: 'assistant', content: answer }])
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: "Sorry, I ran into an issue finding the answer." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto mt-20 mb-32 border-t border-border/50 pt-16">
      <h2 className="font-display text-2xl font-bold text-white mb-6 text-center">Ask About This Video</h2>
      
      <div className="bg-white/[0.02] border border-border rounded-2xl flex flex-col h-[600px] overflow-hidden backdrop-blur-md relative">
        {/* Top Toggle */}
        <div className="p-4 border-b border-border bg-black/20 flex flex-col items-center shrink-0">
          <div className="flex bg-white/5 p-1 rounded-full border border-white/10 mb-2">
            <button 
              onClick={() => setChatMode('strict')}
              className={cn("px-4 py-2 rounded-full text-sm font-semibold transition-all outline-none", chatMode === 'strict' ? "bg-gradient-primary text-white" : "text-muted hover:text-white")}
            >
              From this video
            </button>
            <button 
              onClick={() => setChatMode('open')}
              className={cn("px-4 py-2 rounded-full text-sm font-semibold transition-all outline-none", chatMode === 'open' ? "bg-gradient-primary text-white" : "text-muted hover:text-white")}
            >
              Topic chat
            </button>
          </div>
          <p className="text-xs text-muted">
            {chatMode === 'strict' ? "Answers come only from this video's transcript." : "Can go deeper. Extra knowledge is labelled [Beyond the video:]"}
          </p>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-3 opacity-80">
              {getStaterChips().map((chip, i) => (
                <button 
                  key={i} 
                  onClick={() => handleSend(chip)}
                  className="bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 py-2 px-5 rounded-full text-sm transition-colors outline-none"
                >
                  {chip}
                </button>
              ))}
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={cn("flex w-full", m.role === 'user' ? "justify-end" : "justify-start")}>
                <div className={cn(
                  "max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed",
                  m.role === 'user' ? "bg-gradient-primary text-white" : "bg-white/5 border border-white/10 text-white/90"
                )}>
                  {m.content}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex w-full justify-start">
              <div className="bg-white/5 border border-white/10 rounded-2xl px-5 py-3 text-sm text-muted animate-pulse">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-border bg-black/20 shrink-0">
          <form onSubmit={e => { e.preventDefault(); handleSend(input); }} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="w-full bg-black/50 border border-white/10 rounded-xl py-4 pl-4 pr-24 text-white text-sm focus:outline-none focus:border-primary/50 transition-colors"
            />
            <Button 
              type="submit" 
              variant="gradient" 
              size="sm" 
              className="absolute right-2 px-4 rounded-lg"
              disabled={loading || !input.trim()}
            >
              Ask <Send className="w-3 h-3 ml-2" />
            </Button>
          </form>
          {messages.length > 0 && (
            <button onClick={() => setMessages([])} className="mt-3 text-xs text-muted hover:text-white flex items-center justify-center w-full transition-colors outline-none">
              <Trash className="w-3 h-3 mr-1" /> Clear conversation
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
