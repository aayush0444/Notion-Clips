"use client"
import { useState } from 'react'
import { StudyInsights } from '@/lib/types'
import { ChevronDown, ChevronUp } from 'lucide-react'
import ExportButtons from '@/components/ExportButtons'

export function StudyModeView({ data, sourceUrl }: { data: StudyInsights; sourceUrl?: string }) {
  const [expandedQuestions, setExpandedQuestions] = useState<number[]>([])

  const toggleQuestion = (index: number) => {
    setExpandedQuestions(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-[#E9F0FB] border border-[#C8D9F2] rounded-lg p-6">
        <div className="text-xs text-[#2F4E77] mb-2 uppercase tracking-wider">Core Concept</div>
        <div className="text-foreground/90 leading-relaxed text-sm">
          {data.core_concept || "No core concept available."}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Formula Sheet</div>
        <div className="bg-card border border-border rounded-lg p-6 font-mono text-sm space-y-3">
          {data.formula_sheet?.length ? data.formula_sheet.map((formula, i) => (
            <div key={i} className="text-[#5A8A63]">{formula}</div>
          )) : <div className="text-muted">No formulas found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Key Facts</div>
        <div className="space-y-2">
          {data.key_facts?.length ? data.key_facts.map((fact, i) => (
            <div key={i} className="flex gap-3 text-foreground/75 text-sm">
              <span className="text-muted font-mono">{i + 1}.</span>
              <span>{fact}</span>
            </div>
          )) : <div className="text-muted text-sm">No key facts found.</div>}
        </div>
      </div>

      <div className="bg-[#F5F0E8] border border-border rounded-lg p-4">
        <div className="text-xs app-text-muted mb-2 uppercase tracking-wider">How to Use These Notes</div>
        <div className="text-sm text-foreground/75 leading-relaxed">
          Revise in this order: core concept → formulas → key facts → self-test. If you miss a question, revisit the related key fact before moving forward.
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Common Mistakes</div>
        <div className="space-y-2">
          {data.common_mistakes?.length ? data.common_mistakes.map((mistake, i) => (
            <div key={i} className="flex gap-3 text-[#9E6B2E] text-sm">
              <span className="text-[#C68835]">⚠</span>
              <span>{mistake}</span>
            </div>
          )) : <div className="text-muted text-sm">No common mistakes identified.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Self-Test Questions</div>
        <div className="space-y-2">
          {data.self_test?.length ? data.self_test.map((question, i) => (
            <div key={i} className="bg-card border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleQuestion(i)}
                className="w-full px-4 py-3 flex items-center justify-between text-sm text-foreground/90 hover:bg-[#F5F0E8] transition-colors"
              >
                <span>{question}</span>
                {expandedQuestions.includes(i) ? (
                  <ChevronUp className="w-4 h-4 text-muted" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted" />
                )}
              </button>
              {expandedQuestions.includes(i) && (
                <div className="px-4 pb-3 pt-1 text-sm app-text-muted leading-relaxed border-t border-border/70">
                  Reflect on this question using the video transcript context.
                </div>
              )}
            </div>
          )) : <div className="text-muted text-sm">No self-test questions found.</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Prerequisites</div>
          <div className="flex flex-wrap gap-2">
            {data.prerequisites?.length ? data.prerequisites.map((item, i) => (
              <div key={i} className="px-2.5 py-1 rounded-md border border-border bg-[#F5F0E8] text-xs text-foreground/75">
                {item}
              </div>
            )) : <div className="text-muted text-sm">No prerequisites listed.</div>}
          </div>
        </div>
        <div>
          <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Further Reading</div>
          <div className="flex flex-wrap gap-2">
            {data.further_reading?.length ? data.further_reading.map((item, i) => (
              <div key={i} className="px-2.5 py-1 rounded-md border border-border bg-[#F5F0E8] text-xs text-foreground/75">
                {item}
              </div>
            )) : <div className="text-muted text-sm">No further reading links found.</div>}
          </div>
        </div>
      </div>

      {/* Export buttons */}
      <div className="mt-8 pt-6 border-t border-border">
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Export Options</div>
        <ExportButtons results={data} sourceUrl={sourceUrl} mode="study" />
      </div>
    </div>
  )
}
