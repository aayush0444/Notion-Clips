"use client"
import { useAppStore } from '@/lib/store'
import { Button } from '@/components/ui/Button'
import { Zap } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'

export function ConnectionBanner() {
  const { isConnected, sessionId } = useAppStore()

  const handleConnect = () => {
    if (!sessionId) return
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/notion?session_id=${sessionId}`
  }

  return (
    <AnimatePresence>
      {!isConnected && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
          className="w-full bg-primary/10 border-b border-primary/20 p-3 flex items-center justify-center mb-6 z-40 relative"
        >
          <div className="flex items-center space-x-4 max-w-2xl mx-auto w-full px-4 sm:px-6">
            <Zap className="h-5 w-5 text-primary shrink-0" />
            <span className="text-sm font-medium text-white/90 truncate flex-1">
              Connect your Notion workspace to push notes automatically
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleConnect}
              className="shrink-0 bg-background hover:bg-white/10 text-primary border-primary/30"
            >
              Connect Notion →
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
