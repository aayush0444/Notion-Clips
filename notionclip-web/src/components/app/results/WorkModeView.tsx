"use client"
import { WorkInsights } from '@/lib/types'
import { CheckSquare, Square } from 'lucide-react'
import { useState } from 'react'

export function WorkModeView({ data }: { data: WorkInsights }) {
  const [checkedItems, setCheckedItems] = useState<number[]>([])

  const toggleCheck = (index: number) => {
    setCheckedItems(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 border ${
          data.watch_or_skip?.toLowerCase().includes('watch')
            ? 'bg-green-500/20 border-green-500/30'
            : 'bg-red-500/20 border-red-500/30'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            data.watch_or_skip?.toLowerCase().includes('watch') ? 'bg-green-400' : 'bg-red-400'
          }`} />
          <span className={`font-medium ${
            data.watch_or_skip?.toLowerCase().includes('watch') ? 'text-green-300' : 'text-red-300'
          }`}>
            {data.watch_or_skip || "Verdict unavailable"}
          </span>
        </div>
        <div className="text-xs text-white/40">Based on relevance and content quality</div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-2 uppercase tracking-wider">Summary</div>
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
    </div>
  )
}
