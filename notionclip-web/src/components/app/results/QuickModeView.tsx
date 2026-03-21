"use client"
import { useState } from 'react'
import { QuickInsights } from '@/lib/types'
import { Tabs, TabContent } from '@/components/ui/Tabs'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Zap } from 'lucide-react'

export function QuickModeView({ data }: { data: QuickInsights }) {
  const [activeTab, setActiveTab] = useState('Takeaways')

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-8 fade-in duration-500 w-full max-w-3xl mx-auto">
      <Card className="bg-primary/5 border-primary/20 shadow-[0_0_40px_rgba(96,165,250,0.05)]">
        <CardHeader className="pb-6">
          <div className="flex items-center space-x-2 mb-3">
            <Zap className="h-5 w-5 text-primary" />
            <span className="text-primary/90 text-xs font-bold tracking-wider uppercase">The Gist</span>
          </div>
          <CardTitle className="text-2xl leading-relaxed text-white font-medium">{data.summary}</CardTitle>
        </CardHeader>
      </Card>

      <div>
        <Tabs 
          tabs={['Takeaways', 'Topics']} 
          activeTab={activeTab} 
          onChange={setActiveTab} 
        />
        
        <TabContent isActive={activeTab === 'Takeaways'}>
          <ul className="space-y-3 mt-4">
            {data.key_takeaways?.map((ta, i) => (
              <li key={i} className="flex items-start bg-white/[0.02] border border-border rounded-lg p-4 text-white/90">
                <span className="mr-3 mt-1.5 block h-1.5 w-1.5 rounded-full bg-primary/80 shrink-0" />
                <span className="leading-relaxed">{ta}</span>
              </li>
            ))}
          </ul>
        </TabContent>

        <TabContent isActive={activeTab === 'Topics'}>
          <div className="flex flex-wrap gap-2 mt-4">
            {data.topics_covered?.map((topic, i) => (
              <span key={i} className="bg-white/5 border border-white/10 text-white/80 rounded-full px-4 py-1.5 text-sm">
                {topic}
              </span>
            ))}
          </div>
        </TabContent>
      </div>
    </div>
  )
}
