"use client"
import { useState } from 'react'
import { StudyInsights } from '@/lib/types'
import { ChevronDown, ChevronUp } from 'lucide-react'

export function StudyModeView({ data }: { data: StudyInsights }) {
  const [expandedQuestions, setExpandedQuestions] = useState<number[]>([])

  const toggleQuestion = (index: number) => {
    setExpandedQuestions(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
        <div className="text-xs text-blue-400 mb-2 uppercase tracking-wider">Core Concept</div>
        <div className="text-white/90 leading-relaxed text-sm">
          {data.core_concept || "No core concept available."}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Formula Sheet</div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 font-mono text-sm space-y-3">
          {data.formula_sheet?.length ? data.formula_sheet.map((formula, i) => (
            <div key={i} className="text-green-400">{formula}</div>
          )) : <div className="text-white/50">No formulas found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Key Facts</div>
        <div className="space-y-2">
          {data.key_facts?.length ? data.key_facts.map((fact, i) => (
            <div key={i} className="flex gap-3 text-white/70 text-sm">
              <span className="text-white/40 font-mono">{i + 1}.</span>
              <span>{fact}</span>
            </div>
          )) : <div className="text-white/50 text-sm">No key facts found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Common Mistakes</div>
        <div className="space-y-2">
          {data.common_mistakes?.length ? data.common_mistakes.map((mistake, i) => (
            <div key={i} className="flex gap-3 text-orange-300/70 text-sm">
              <span className="text-orange-400/60">⚠</span>
              <span>{mistake}</span>
            </div>
          )) : <div className="text-white/50 text-sm">No common mistakes identified.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Self-Test Questions</div>
        <div className="space-y-2">
          {data.self_test?.length ? data.self_test.map((question, i) => (
            <div key={i} className="bg-white/5 border border-white/10 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleQuestion(i)}
                className="w-full px-4 py-3 flex items-center justify-between text-sm text-white/90 hover:bg-white/5 transition-colors"
              >
                <span>{question}</span>
                {expandedQuestions.includes(i) ? (
                  <ChevronUp className="w-4 h-4 text-white/40" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/40" />
                )}
              </button>
              {expandedQuestions.includes(i) && (
                <div className="px-4 pb-3 pt-1 text-sm text-white/60 leading-relaxed border-t border-white/5">
                  Reflect on this question using the video transcript context.
                </div>
              )}
            </div>
          )) : <div className="text-white/50 text-sm">No self-test questions found.</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Prerequisites</div>
          <div className="space-y-2">
            {data.prerequisites?.length ? data.prerequisites.map((item, i) => (
              <div key={i} className="text-sm text-white/70">{item}</div>
            )) : <div className="text-white/50 text-sm">No prerequisites listed.</div>}
          </div>
        </div>
        <div>
          <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Further Reading</div>
          <div className="space-y-2">
            {data.further_reading?.length ? data.further_reading.map((item, i) => (
              <div key={i} className="text-sm text-white/70">{item}</div>
            )) : <div className="text-white/50 text-sm">No further reading links found.</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
