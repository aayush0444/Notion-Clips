"use client"
import { useAppStore } from '@/lib/store'
import { Youtube, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function UrlInput() {
  const { url, setUrl, setVideoId, videoId } = useAppStore()

  const extractId = (text: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
    const match = text.match(regExp)
    return (match && match[2].length === 11) ? match[2] : null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value)
    const id = extractId(e.target.value)
    setVideoId(id)
  }

  return (
    <div className="w-full mb-8">
      <label className="block text-sm font-medium text-muted mb-2 font-sans">
        YouTube URL
      </label>
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Youtube className="h-6 w-6 text-red-500/80 group-focus-within:text-red-500 transition-colors" />
        </div>
        <input
          type="text"
          value={url}
          onChange={handleChange}
          placeholder="https://www.youtube.com/watch?v=..."
          className="block w-full rounded-xl border border-white/10 bg-white/5 py-4 pl-12 pr-4 text-white placeholder-muted transition-colors sm:text-lg focus:outline-none focus:border-white/20 hover:bg-white/10"
        />
        <AnimatePresence>
          {videoId && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center bg-success/20 text-success text-xs font-semibold px-2 py-1.5 rounded-md border border-success/20"
            >
              <Check className="h-3 w-3 mr-1" />
              ID: {videoId}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
