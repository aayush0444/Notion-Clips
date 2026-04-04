"use client"
import { QuickInsights } from '@/lib/types'
import ExportButtons from '@/components/ExportButtons'
import { TimestampMomentsPanel } from './TimestampMomentsPanel'

export function QuickModeView({
  data,
  sourceUrl,
  sessionId,
  notionPageId,
}: {
  data: QuickInsights
  sourceUrl?: string
  sessionId?: string | null
  notionPageId?: string | null
}) {
  return (
    <div className="space-y-6">
      <TimestampMomentsPanel
        data={data}
        sourceUrl={sourceUrl}
        mode="quick"
        sessionId={sessionId}
        notionPageId={notionPageId}
        aiSummary={data.summary}
        videoTitle={data.title}
      />

      <div className="bg-[#F1E8F6] border border-[#D9C2E8] rounded-lg p-5">
        <div className="text-xs text-[#7A5BB5] mb-2 uppercase tracking-wider">Quick Brief</div>
        <div className="text-foreground/90 text-sm leading-relaxed">
          {data.title || "Fast, high-signal summary of this video."}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Summary</div>
        <div className="text-foreground/90 leading-relaxed text-sm">{data.summary || "No summary available."}</div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Key Takeaways</div>
        <div className="space-y-3">
          {data.key_takeaways?.length ? data.key_takeaways.map((takeaway, i) => (
            <div key={i} className="flex gap-3 items-start">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#E9F0FB] to-[#F1E8F6] border border-border flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs text-foreground/55">{i + 1}</span>
              </div>
              <div className="text-foreground/80 text-sm leading-relaxed">{takeaway}</div>
            </div>
          )) : <div className="text-muted text-sm">No takeaways found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Topics Covered</div>
        <div className="flex flex-wrap gap-2">
          {data.topics_covered?.length ? data.topics_covered.map((topic, i) => (
            <div key={i} className="px-3 py-1.5 bg-gradient-to-br from-[#E9F0FB] to-[#F1E8F6] border border-border rounded-md text-xs text-foreground/70">
              {topic}
            </div>
          )) : <div className="text-muted text-sm">No topics found.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Action Items</div>
        <div className="space-y-2">
          {data.action_items?.length ? data.action_items.map((item, i) => (
            <div key={i} className="flex gap-3 text-foreground/75 text-sm items-start">
              <span className="text-[#5A8A63] mt-0.5">✓</span>
              <span>{item}</span>
            </div>
          )) : <div className="text-muted text-sm">No action items suggested.</div>}
        </div>
      </div>

      <div>
        <div className="text-xs app-text-muted mb-3 uppercase tracking-wider">Export Options</div>
        <ExportButtons results={data} sourceUrl={sourceUrl} mode="quick" />
      </div>
    </div>
  )
}
