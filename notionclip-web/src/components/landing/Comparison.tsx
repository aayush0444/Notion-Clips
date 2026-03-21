"use client"

import { motion } from 'framer-motion'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { X, Check } from 'lucide-react'

export function Comparison() {
  return (
    <div className="py-24 bg-white/[0.02] border-y border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold sm:text-4xl text-white tracking-tight">
            Why not just use ChatGPT?
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* ChatGPT limitations */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <Card className="h-full bg-black/40 border-white/5 opacity-80 backdrop-blur-md">
              <CardHeader>
                <CardTitle className="text-muted text-lg tracking-normal">Generic AI Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4">
                  {[
                    "Unstructured bullet points",
                    "Same format for every video",
                    "No Notion integration",
                    "Loses context on long videos",
                    "No way to verify claims"
                  ].map((item, i) => (
                    <li key={i} className="flex items-center text-muted">
                      <X className="h-5 w-5 mr-3 text-red-500/80 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
          
          {/* NotionClip benefits */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="h-full border-primary/30 bg-primary/5 shadow-[0_0_30px_rgba(96,165,250,0.05)] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <div className="w-32 h-32 bg-primary rounded-full blur-[60px]" />
              </div>
              <CardHeader>
                <CardTitle className="text-white tracking-normal drop-shadow-sm">NotionClip — Study Mode</CardTitle>
              </CardHeader>
              <CardContent className="relative z-10">
                <ul className="space-y-4">
                  <li className="flex items-start text-white/90">
                    <Check className="h-5 w-5 mr-3 text-success shrink-0 mt-0.5" />
                    <span>Formula sheet: <code className="font-mono text-xs bg-white/10 px-1.5 py-0.5 rounded ml-1 text-primary-50">a·sinθ = nλ</code> where a is slit width</span>
                  </li>
                  {[
                    "44 key facts extracted from a 2-hour lecture",
                    "Self-test question: condition for destructive interference",
                    "Fact timestamped at approximately 08:30",
                    "Pushed to Notion with toggle blocks"
                  ].map((item, i) => (
                    <li key={i} className="flex items-start text-white/90">
                      <Check className="h-5 w-5 mr-3 text-success shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
