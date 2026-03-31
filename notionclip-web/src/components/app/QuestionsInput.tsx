"use client"

import { Lightbulb, X } from 'lucide-react'
import { useState } from 'react'

export function QuestionsInput({
  questions,
  onChange,
}: {
  questions: string[]
  onChange: (questions: string[]) => void
}) {
  const [input, setInput] = useState("")
  const [isOpen, setIsOpen] = useState(false)

  const handleAddQuestion = () => {
    const trimmed = input.trim()
    if (trimmed && !questions.includes(trimmed)) {
      onChange([...questions, trimmed])
      setInput("")
    }
  }

  const handleRemoveQuestion = (index: number) => {
    onChange(questions.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAddQuestion()
    }
  }

  return (
    <div className="space-y-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-4 py-3 rounded-lg bg-card border border-border hover:border-border-hover transition-colors text-sm text-foreground/85 hover:text-foreground"
      >
        <Lightbulb className="w-4 h-4 text-[#D19A28]" />
        <span>{questions.length === 0 ? "Ask specific questions (optional)" : `${questions.length} question${questions.length !== 1 ? 's' : ''}`}</span>
      </button>

      {isOpen && (
        <div className="space-y-3 p-4 rounded-lg bg-card border border-border">
          <div className="text-xs app-text-muted mb-3">
            Ask questions to focus extraction on what matters to you
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g., How do I set up authentication?"
              className="flex-1 px-3 py-2 bg-[#FCFAF7] border border-border rounded-md text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-border-hover transition-colors"
            />
            <button
              onClick={handleAddQuestion}
              disabled={!input.trim()}
              className="px-3 py-2 bg-[#EDE6FA] border border-[#CDBAEF] rounded-md text-sm text-[#7A5BB5] hover:bg-[#E4D9F5] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Add
            </button>
          </div>

          {questions.length > 0 && (
            <div className="space-y-2">
              {questions.map((q, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-md bg-[#F5F0E8] border border-border"
                >
                  <div className="flex-1 text-sm text-foreground/90 pt-0.5">{q}</div>
                  <button
                    onClick={() => handleRemoveQuestion(idx)}
                    className="text-muted hover:text-foreground/60 transition-colors flex-shrink-0"
                    aria-label="Remove question"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {questions.length > 0 && (
            <button
              onClick={() => onChange([])}
              className="w-full text-xs app-text-muted hover:text-foreground/65 transition-colors py-2"
            >
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  )
}
