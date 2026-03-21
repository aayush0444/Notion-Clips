"use client"
import { useState } from 'react'
import { WorkInsights } from '@/lib/types'
import { Tabs, TabContent } from '@/components/ui/Tabs'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react'

export function WorkModeView({ data }: { data: WorkInsights }) {
  const [activeTab, setActiveTab] = useState('Key Points')
  
  const isWatch = data.watch_or_skip?.toLowerCase().startsWith('watch')
  const VerdictIcon = isWatch ? CheckCircle : XCircle
  const verdictColor = isWatch ? "text-success bg-success/10 border-success/20 shadow-[0_0_40px_rgba(52,211,153,0.05)]" : "text-danger bg-danger/10 border-danger/20 shadow-[0_0_40px_rgba(248,113,113,0.05)]"

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-8 fade-in duration-500 w-full max-w-3xl mx-auto">
      <Card className={`border ${verdictColor}`}>
        <CardHeader className="pb-6">
          <div className="flex items-center space-x-3 mb-3">
            <VerdictIcon className={`h-8 w-8 ${isWatch ? 'text-success' : 'text-danger'}`} />
            <span className={`text-sm font-bold tracking-wider uppercase ${isWatch ? 'text-success/80' : 'text-danger/80'}`}>
              Verdict
            </span>
          </div>
          <CardTitle className="text-3xl sm:text-4xl leading-tight text-white">{data.watch_or_skip}</CardTitle>
          {data.one_liner && (
            <p className="text-xl text-white/70 italic mt-6 border-l-2 border-white/20 pl-4">
              &quot;{data.one_liner}&quot;
            </p>
          )}
        </CardHeader>
      </Card>

      <div>
        <Tabs 
          tabs={['Key Points', 'Tools', 'Decisions', 'Actions']} 
          activeTab={activeTab} 
          onChange={setActiveTab} 
        />
        
        <TabContent isActive={activeTab === 'Key Points'}>
          <ul className="space-y-3 mt-4">
            {data.key_points?.map((kp, i) => (
              <li key={i} className="flex items-start bg-white/[0.02] border border-border rounded-lg p-4 text-white/90">
                <span className="mr-3 mt-1.5 block h-1.5 w-1.5 rounded-full bg-primary/80 shrink-0" />
                <span className="leading-relaxed">{kp}</span>
              </li>
            ))}
          </ul>
        </TabContent>

        <TabContent isActive={activeTab === 'Tools'}>
          <div className="flex flex-wrap gap-3 mt-4">
            {data.tools_mentioned?.length ? data.tools_mentioned.map((tool, i) => (
              <Badge key={i} variant="secondary" className="text-sm px-3 py-1 font-mono">{tool}</Badge>
            )) : <p className="text-muted italic">No specific tools mentioned.</p>}
          </div>
        </TabContent>

        <TabContent isActive={activeTab === 'Decisions'}>
          <div className="space-y-3 mt-4">
            {data.decisions_to_make?.map((dec, i) => (
              <label key={i} className="flex items-start bg-white/[0.02] border border-border rounded-lg p-4 cursor-pointer hover:bg-white-[0.04] transition-colors">
                <input type="checkbox" className="mt-1 mr-4 h-4 w-4 rounded border-border bg-white/5 text-primary focus:ring-primary/50 focus:ring-1" />
                <span className="text-white/90 leading-relaxed">{dec}</span>
              </label>
            ))}
          </div>
        </TabContent>

        <TabContent isActive={activeTab === 'Actions'}>
          <div className="space-y-3 mt-4">
            {data.next_actions?.map((act, i) => (
              <div key={i} className="flex items-start bg-white/[0.02] border border-border rounded-lg p-4">
                <ArrowRight className="h-5 w-5 text-primary mr-3 shrink-0 mt-0.5" />
                <span className="text-white/90 leading-relaxed">{act}</span>
              </div>
            ))}
          </div>
        </TabContent>
      </div>
    </div>
  )
}
