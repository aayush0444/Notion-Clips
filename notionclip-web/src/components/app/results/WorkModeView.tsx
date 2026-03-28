"use client"
import { WorkInsights } from '@/lib/types'
import { CheckSquare, Square } from 'lucide-react'
import { useState } from 'react'
import ExportButtons from '@/components/ExportButtons'

export function WorkModeView({ data, sourceUrl }: { data: WorkInsights; sourceUrl?: string }) {
  const [checkedItems, setCheckedItems] = useState<number[]>([])
  const recommendation = data.recommendation || data.watch_or_skip || "Recommendation unavailable"
  const isWatch = recommendation.toLowerCase().startsWith("watch")

  const toggleCheck = (index: number) => {
    setCheckedItems(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 border ${
          isWatch
            ? 'bg-green-500/20 border-green-500/30'
            : 'bg-red-500/20 border-red-500/30'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            isWatch ? 'bg-green-400' : 'bg-red-400'
          }`} />
          <span className={`font-medium ${
            isWatch ? 'text-green-300' : 'text-red-300'
          }`}>
            {recommendation}
          </span>
        </div>
        <div className="text-xs text-white/40">Based on relevance and content quality</div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-2 uppercase tracking-wider">One-Liner</div>
        <div className="text-white/90 text-base leading-relaxed">
          {data.one_liner || "No summary available."}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Key Points</div>
        <div className="space-y-2">
          {data.key_points?.length ? data.key_points.map((point, i) => (
            <div key={i} className="flex gap-3 text-white/70 text-sm items-start">
              <span className="text-purple-400 mt-1">•</span>
              <span>{point}</span>
            </div>
          )) : <div className="text-white/50 text-sm">No key points found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Tools Mentioned</div>
        <div className="flex flex-wrap gap-2">
          {data.tools_mentioned?.length ? data.tools_mentioned.map((tool, i) => (
            <div key={i} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-md text-xs text-white/70">
              {tool}
            </div>
          )) : <div className="text-white/50 text-sm">No tools mentioned.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Decisions to Make</div>
        <div className="space-y-2">
          {data.decisions_to_make?.length ? data.decisions_to_make.map((decision, i) => (
            <div key={i} className="flex gap-3 text-white/80 text-sm items-start">
              <span className="text-yellow-400 mt-0.5">→</span>
              <span>{decision}</span>
            </div>
          )) : <div className="text-white/50 text-sm">No explicit decisions identified.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Action Items</div>
        <div className="space-y-2">
          {data.next_actions?.length ? data.next_actions.map((item, i) => (
            <button
              key={i}
              onClick={() => toggleCheck(i)}
              className="w-full flex items-start gap-3 text-left text-sm text-white/70 hover:text-white/90 transition-colors group"
            >
              {checkedItems.includes(i) ? (
                <CheckSquare className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
              ) : (
                <Square className="w-5 h-5 text-white/30 group-hover:text-white/50 mt-0.5 flex-shrink-0" />
              )}
              <span className={checkedItems.includes(i) ? 'line-through text-white/40' : ''}>
                {item}
              </span>
            </button>
          )) : <div className="text-white/50 text-sm">No action items found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Export Options</div>
        <ExportButtons results={data} sourceUrl={sourceUrl} mode="work" />
      </div>
    </div>
  )
}
