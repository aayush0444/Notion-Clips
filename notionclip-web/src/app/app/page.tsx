"use client"
import { AppHeader } from '@/components/layout/AppHeader'
import { ConnectionBanner } from '@/components/app/ConnectionBanner'
import { UrlInput } from '@/components/app/UrlInput'
import { ModeSelector } from '@/components/app/ModeSelector'
import { ProcessButton } from '@/components/app/ProcessButton'
import { MetricStrip } from '@/components/app/results/MetricStrip'
import { StudyModeView } from '@/components/app/results/StudyModeView'
import { WorkModeView } from '@/components/app/results/WorkModeView'
import { QuickModeView } from '@/components/app/results/QuickModeView'
import { QnASection } from '@/components/app/QnASection'
import { useAppStore } from '@/lib/store'
import { Button } from '@/components/ui/Button'
import { api } from '@/lib/api'
import { Check, UploadCloud } from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function AppPage() {
  const { results, mode, url, sessionId, isConnected } = useAppStore()
  const [pushing, setPushing] = useState(false)
  const [pushed, setPushed] = useState(false)

  const handlePush = async () => {
    if (!sessionId || !url || !results) return
    setPushing(true)
    try {
      await api.pushToNotion(mode, results, url, sessionId)
      setPushed(true)
      setTimeout(() => setPushed(false), 3000)
    } catch (err) {
      console.error(err)
    } finally {
      setPushing(false)
    }
  }

  return (
    <>
      <AppHeader />
      <main className="flex-1 pt-24 pb-20 relative z-10 w-full">
        <ConnectionBanner />
        
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <UrlInput />
          <ModeSelector />
          <ProcessButton />
          
          <AnimatePresence mode="wait">
            {results && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
                className="mt-16 w-full"
              >
                <MetricStrip />
                
                {mode === 'study' && <StudyModeView data={results} />}
                {mode === 'work' && <WorkModeView data={results} />}
                {mode === 'quick' && <QuickModeView data={results} />}
                
                <div className="mt-12 w-full max-w-3xl mx-auto">
                  <Button 
                    variant="gradient" 
                    size="lg" 
                    className="w-full text-lg h-14 tracking-wide relative overflow-hidden group"
                    disabled={!isConnected || pushing || pushed}
                    onClick={handlePush}
                    title={!isConnected ? "Connect Notion first" : ""}
                  >
                    {!isConnected && <div className="absolute inset-0 bg-black/50 z-10" />}
                    {pushed ? (
                      <><Check className="mr-2 h-5 w-5" /> Saved to Notion</>
                    ) : pushing ? (
                      "Saving to Notion..."
                    ) : (
                      <><UploadCloud className="mr-2 h-5 w-5" /> Save to Notion</>
                    )}
                  </Button>
                  {!isConnected && (
                    <p className="text-center text-sm text-danger mt-3">
                      Please connect Notion using the banner above.
                    </p>
                  )}
                </div>
                
                <QnASection />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </>
  )
}
