"use client"
import { useState } from 'react'
import { StudyInsights } from '@/lib/types'
import { Tabs, TabContent } from '@/components/ui/Tabs'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { AlertCircle, ChevronDown, Copy } from 'lucide-react'

export function StudyModeView({ data }: { data: StudyInsights }) {
  const [activeTab, setActiveTab] = useState('Formulas')

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code)
  }

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-8 fade-in duration-500 w-full max-w-3xl mx-auto">
      <Card className="bg-yellow-500/10 border-yellow-500/20 shadow-[0_0_40px_rgba(234,179,8,0.05)]">
        <CardHeader className="pb-6">
          <span className="text-yellow-500/80 text-xs font-bold tracking-wider uppercase mb-3 block">Core Concept</span>
          <CardTitle className="text-3xl sm:text-4xl leading-tight text-white">{data.core_concept || "N/A"}</CardTitle>
        </CardHeader>
      </Card>

      <div>
        <Tabs 
          tabs={['Formulas', 'Key Facts', 'Mistakes', 'Self-Test', 'Resources']} 
          activeTab={activeTab} 
          onChange={setActiveTab} 
        />
        
        <TabContent isActive={activeTab === 'Formulas'}>
          <p className="text-sm text-muted mb-4">Definitions of every variable are included.</p>
          <div className="space-y-4">
            {data.formula_sheet?.map((f, i) => (
              <div key={i} className="relative group bg-black/40 border border-white/5 rounded-lg p-4 font-mono text-sm text-primary-50">
                {f}
                <button onClick={() => copyCode(f)} className="absolute right-3 top-3 p-1.5 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md hover:bg-white/10">
                  <Copy className="h-4 w-4 text-muted" />
                </button>
              </div>
            ))}
          </div>
        </TabContent>

        <TabContent isActive={activeTab === 'Key Facts'}>
          <p className="text-sm text-muted mb-4">Timestamps show where in the video each fact appears.</p>
          <ul className="space-y-3">
            {data.key_facts?.map((fact, i) => (
              <li key={i} className="flex font-sans text-white/90 bg-white/[0.02] border border-border rounded-lg p-4">
                <span className="text-muted mr-4 font-mono">{i+1}.</span>
                <span dangerouslySetInnerHTML={{__html: fact.replace(/(\d{1,2}:\d{2})/g, '<span class="text-primary font-mono bg-primary/10 px-1 rounded mx-1">$1</span>')}} />
              </li>
            ))}
          </ul>
        </TabContent>

        <TabContent isActive={activeTab === 'Mistakes'}>
          {!data.common_mistakes?.length ? (
            <p className="text-muted italic">No common mistakes identified for this video.</p>
          ) : (
            <div className="space-y-3">
              {data.common_mistakes.map((mistake, i) => (
                <div key={i} className="flex items-start bg-danger/5 border border-danger/10 rounded-lg p-4">
                  <AlertCircle className="h-5 w-5 text-danger mr-3 shrink-0 mt-0.5" />
                  <span className="text-white/90">{mistake}</span>
                </div>
              ))}
            </div>
          )}
        </TabContent>

        <TabContent isActive={activeTab === 'Self-Test'}>
          <p className="text-sm text-muted mb-4">Write your answer before expanding.</p>
          <div className="space-y-4">
            {data.self_test?.map((q, i) => (
              <details key={i} className="group bg-white/[0.02] border border-border rounded-lg [&_summary::-webkit-details-marker]:hidden">
                <summary className="flex cursor-pointer items-center justify-between p-4 font-medium text-white/90">
                  {q}
                  <ChevronDown className="h-5 w-5 text-muted transition-transform group-open:-rotate-180" />
                </summary>
                <div className="p-4 pt-0">
                  <textarea 
                    placeholder="Type your answer here..." 
                    className="w-full bg-black/40 border border-white/5 rounded-md p-3 text-sm text-white placeholder-muted focus:outline-none focus:border-primary/50 min-h-[80px]"
                  />
                </div>
              </details>
            ))}
          </div>
        </TabContent>

        <TabContent isActive={activeTab === 'Resources'}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-lg">Prerequisites</CardTitle></CardHeader>
              <CardContent>
                <ul className="list-disc pl-5 space-y-2 text-white/80 text-sm">
                  {data.prerequisites?.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-lg">Further Reading</CardTitle></CardHeader>
              <CardContent>
                <ul className="list-disc pl-5 space-y-2 text-white/80 text-sm">
                  {data.further_reading?.map((fr, i) => <li key={i}>{fr}</li>)}
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabContent>
      </div>
    </div>
  )
}
