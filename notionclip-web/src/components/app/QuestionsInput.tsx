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
        className="w-full flex items-center gap-2 px-4 py-3 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 transition-colors text-sm text-white/80 hover:text-white/90"
      >
        <Lightbulb className="w-4 h-4 text-amber-400" />
        <span>{questions.length === 0 ? "Ask specific questions (optional)" : `${questions.length} question${questions.length !== 1 ? 's' : ''}`}</span>
      </button>

      {isOpen && (
        <div className="space-y-3 p-4 rounded-lg bg-white/5 border border-white/10">
          <div className="text-xs text-white/50 mb-3">
            Ask questions to focus extraction on what matters to you
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g., How do I set up authentication?"
              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-md text-sm text-white placeholder-white/40 focus:outline-none focus:border-primary/50 transition-colors"
            />
            <button
              onClick={handleAddQuestion}
              disabled={!input.trim()}
              className="px-3 py-2 bg-primary/20 border border-primary/30 rounded-md text-sm text-primary hover:bg-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Add
            </button>
          </div>

          {questions.length > 0 && (
            <div className="space-y-2">
              {questions.map((q, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-md bg-primary/10 border border-primary/20"
                >
                  <div className="flex-1 text-sm text-white/90 pt-0.5">{q}</div>
                  <button
                    onClick={() => handleRemoveQuestion(idx)}
                    className="text-white/40 hover:text-white/60 transition-colors flex-shrink-0"
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
              className="w-full text-xs text-white/40 hover:text-white/60 transition-colors py-2"
            >
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  )
}
