"use client"

import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Navbar } from "@/components/layout/Navbar"
import { UrlInput } from "@/components/app/UrlInput"
import { ModeSelector } from "@/components/app/ModeSelector"
import { ProcessButton } from "@/components/app/ProcessButton"
import { MetricStrip } from "@/components/app/MetricStrip"
import { StudyModeView } from "@/components/app/results/StudyModeView"
import { WorkModeView } from "@/components/app/results/WorkModeView"
import { QuickModeView } from "@/components/app/results/QuickModeView"
import { QnASection } from "@/components/app/QnASection"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"

const loadingMessagesByStage = {
  transcript: "Fetching transcript...",
  extract: "Extracting insights...",
  finalizing: "Finalizing results..."
} as const

function LoadingPanel({ stage }: { stage: keyof typeof loadingMessagesByStage }) {
  const currentMessage = loadingMessagesByStage[stage]
  const widths = ["100%", "85%", "70%", "90%"]
  return (
    <div className="space-y-5" aria-live="polite">
      <div className="flex items-center space-x-3 text-sm text-white/70">
        <span className="h-2.5 w-2.5 rounded-full bg-primary animate-pulse" />
        <AnimatePresence mode="wait">
          <motion.div
            key={stage}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.3 }}
          >
            {currentMessage}
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="space-y-3">
        {widths.map((w, idx) => (
          <div key={idx} className="relative overflow-hidden rounded-md bg-white/5 h-6" style={{ width: w }}>
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
              initial={{ x: "-100%" }}
              animate={{ x: "100%" }}
              transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
              style={{ width: "120%" }}
            />
            <div style={{ width: w }} className="h-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AppPage() {
  const { results, mode, url, sessionId, isConnected, setNotionPageId } = useAppStore()
  const [pushing, setPushing] = useState(false)
  const [pushError, setPushError] = useState("")
  const [pushSuccess, setPushSuccess] = useState(false)
  const [leftWidth, setLeftWidth] = useState(400)
  const [isResizing, setIsResizing] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStage, setProcessingStage] = useState<keyof typeof loadingMessagesByStage>("transcript")
  const containerRef = useRef<HTMLDivElement>(null)
  const minLeft = 320
  const maxLeft = 520

  useEffect(() => {
    if (!isResizing) return
    const handleMove = (event: PointerEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      let nextWidth = event.clientX - rect.left
      nextWidth = Math.max(minLeft, Math.min(maxLeft, nextWidth))
      setLeftWidth(nextWidth)
    }
    const handleUp = () => setIsResizing(false)
    window.addEventListener("pointermove", handleMove)
    window.addEventListener("pointerup", handleUp)
    document.body.style.userSelect = "none"
    return () => {
      window.removeEventListener("pointermove", handleMove)
      window.removeEventListener("pointerup", handleUp)
      document.body.style.userSelect = ""
    }
  }, [isResizing])

  const handleProcessingChange = (state: boolean) => {
    if (state) setProcessingStage("transcript")
    setIsProcessing(state)
  }

  const handleSaveToNotion = async () => {
    if (!sessionId || !url || !results) return
    setPushing(true)
    setPushError("")
    setPushSuccess(false)
    try {
      const result = await api.pushToNotion(mode, results, url, sessionId)
      setNotionPageId(result.page_id)
      setPushSuccess(true)
      setTimeout(() => setPushSuccess(false), 4000)
    } catch (err: any) {
      setPushError(err?.message || "Failed to push to Notion")
      setPushSuccess(false)
    } finally {
      setPushing(false)
    }
  }

  const handleConnectNotion = () => {
    if (!sessionId) return
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/notion?session_id=${sessionId}`
  }

  return (
    <div className="min-h-screen text-white relative overflow-hidden">
      <Navbar />
      <div className="fixed top-20 right-6 z-[100] space-y-2">
        <AnimatePresence>
          {pushSuccess && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="px-4 py-2 rounded-lg border border-green-500/30 bg-green-500/15 text-green-300 text-sm"
            >
              ✓ Saved to Notion successfully
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {pushError && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="max-w-md px-4 py-2 rounded-lg border border-red-500/30 bg-red-500/15 text-red-300 text-sm"
            >
              ✗ {pushError}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div ref={containerRef} className="pt-16 h-[calc(100vh-0px)] flex">
        <aside
          style={{ width: leftWidth }}
          className="border-r border-white/5 p-8 flex flex-col min-w-[320px] max-w-[520px] h-[calc(100vh-64px)] overflow-y-auto overflow-x-hidden"
        >
          <div className="flex-1 space-y-6">
            <UrlInput />
            <ModeSelector />
            <ProcessButton onProcessingChange={handleProcessingChange} onStageChange={setProcessingStage} />
            <MetricStrip />

            {results && (
              <div className="space-y-2">
                {isConnected ? (
                  <Button
                    variant="gradient"
                    className="w-full py-3.5 text-sm font-medium"
                    onClick={handleSaveToNotion}
                    disabled={pushing}
                  >
                    {pushing ? "Saving..." : "Save to Notion"}
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    className="w-full py-3.5 text-sm font-medium"
                    onClick={handleConnectNotion}
                  >
                    Connect Notion to Save
                  </Button>
                )}
              </div>
            )}
          </div>
        </aside>
        <div
          role="separator"
          aria-orientation="vertical"
          onPointerDown={(event) => {
            event.preventDefault()
            setIsResizing(true)
          }}
          className="w-2 cursor-col-resize bg-white/5 hover:bg-white/10 transition-colors touch-none"
        />

        <section className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto p-8">
            <AnimatePresence mode="wait">
              {isProcessing ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                  className="h-full min-h-[60vh] flex items-center justify-center"
                >
                  <LoadingPanel stage={processingStage} />
                </motion.div>
              ) : !results ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                  className="h-full min-h-[60vh] flex items-center justify-center"
                >
                  <div className="text-center max-w-md">
                    <div className="text-white/40 mb-2">No results yet</div>
                    <div className="text-sm text-white/30">
                      Enter a YouTube URL and click Process Video to generate AI notes
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  {mode === "study" && <StudyModeView data={results} />}
                  {mode === "work" && <WorkModeView data={results} />}
                  {mode === "quick" && <QuickModeView data={results} />}
                  <QnASection />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>
      </div>
    </div>
  )
}
