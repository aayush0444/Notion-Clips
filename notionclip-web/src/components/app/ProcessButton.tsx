"use client"
import { useState } from 'react'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function ProcessButton() {
  const { url, videoId, mode, setResults, setTranscript } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState("")

  const handleProcess = async () => {
    if (!videoId) return
    setLoading(true)
    setResults(null)
    
    try {
      setStep("Fetching transcript...")
      const { transcript } = await api.getTranscript(videoId)
      setTranscript(transcript)

      setStep(`Extracting with ${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode...`)
      const extractRes = await api.extractInsights(transcript, mode)
      
      setStep("Done in 4s")
      setTimeout(() => {
        setResults(extractRes.insights)
        setLoading(false)
        setStep("")
      }, 500)
    } catch (err) {
      console.error(err)
      setStep("Error processing video.")
      setTimeout(() => setLoading(false), 2000)
    }
  }

  return (
    <div className="w-full mb-12">
      <Button 
        variant="gradient" 
        size="lg" 
        className="w-full text-lg font-semibold tracking-wide relative overflow-hidden h-14"
        disabled={!videoId || loading}
        onClick={handleProcess}
      >
        <AnimatePresence mode="wait">
          {!loading ? (
            <motion.span key="normal" initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} exit={{opacity:0, y:-10}}>
              Process Video
            </motion.span>
          ) : (
            <motion.div key="loading" className="flex items-center space-x-3" initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} exit={{opacity:0, y:-10}}>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>{step}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </Button>
    </div>
  )
}
