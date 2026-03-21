"use client"
import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function ProcessButton() {
  const { url, videoId, mode, setResults, setTranscript, setProcessingTime, setWordCount } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    setError("")
  }, [url])

  const handleProcess = async () => {
    if (!videoId) return
    setLoading(true)
    setResults(null)
    setError("")
    
    try {
      const start = Date.now()
      setStep("Fetching transcript...")
      const { transcript } = await api.getTranscript(videoId)
      setTranscript(transcript)

      setStep(`Extracting with ${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode...`)
      const extractRes = await api.extractInsights(transcript, mode)
      
      setProcessingTime(Date.now() - start)
      setWordCount(extractRes.word_count || 0)

      setStep("Done in 4s")
      setTimeout(() => {
        setResults(extractRes.insights)
        setLoading(false)
        setStep("")
      }, 500)
    } catch (err: any) {
      console.error(err)
      setError(err.message || "Failed to process video.")
      setLoading(false)
      setStep("")
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
      {error && <p className="text-center text-sm text-danger mt-3">{error}</p>}
    </div>
  )
}
