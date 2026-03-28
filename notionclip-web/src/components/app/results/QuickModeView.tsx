"use client"
import { QuickInsights } from '@/lib/types'
import ExportButtons from '@/components/ExportButtons'

export function QuickModeView({ data, sourceUrl }: { data: QuickInsights; sourceUrl?: string }) {
  return (
    <div className="space-y-6">
      <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-5">
        <div className="text-xs text-purple-300 mb-2 uppercase tracking-wider">Quick Brief</div>
        <div className="text-white/90 text-sm leading-relaxed">
          {data.title || "Fast, high-signal summary of this video."}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Summary</div>
        <div className="text-white/90 leading-relaxed text-sm">{data.summary || "No summary available."}</div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Key Takeaways</div>
        <div className="space-y-3">
          {data.key_takeaways?.length ? data.key_takeaways.map((takeaway, i) => (
            <div key={i} className="flex gap-3 items-start">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs text-white/60">{i + 1}</span>
              </div>
              <div className="text-white/80 text-sm leading-relaxed">{takeaway}</div>
            </div>
          )) : <div className="text-white/50 text-sm">No takeaways found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Topics Covered</div>
        <div className="flex flex-wrap gap-2">
          {data.topics_covered?.length ? data.topics_covered.map((topic, i) => (
            <div key={i} className="px-3 py-1.5 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/10 rounded-md text-xs text-white/70">
              {topic}
            </div>
          )) : <div className="text-white/50 text-sm">No topics found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Action Items</div>
        <div className="space-y-2">
          {data.action_items?.length ? data.action_items.map((item, i) => (
            <div key={i} className="flex gap-3 text-white/75 text-sm items-start">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>{item}</span>
            </div>
          )) : <div className="text-white/50 text-sm">No action items suggested.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Export Options</div>
        <ExportButtons results={data} sourceUrl={sourceUrl} mode="quick" />
      </div>
    </div>
  )
}
