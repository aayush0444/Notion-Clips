"use client"
import { useState } from 'react'
import { useAppStore } from '@/lib/store'
import { Youtube, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function UrlInput() {
  const { url, setUrl, setVideoId, videoId } = useAppStore()
  const [showUrlAnimation, setShowUrlAnimation] = useState(false)

  const extractId = (text: string) => {
    const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/
    const match = text.match(regExp)
    return (match && match[2].length === 11) ? match[2] : null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value)
    const id = extractId(e.target.value)
    setVideoId(id)
  }

  const handlePaste = () => {
    setShowUrlAnimation(true)
    setTimeout(() => setShowUrlAnimation(false), 2000)
  }

  return (
    <div>
      <label className="block text-xs text-white/40 mb-2 uppercase tracking-wider">
        Video URL
      </label>
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Youtube className="h-5 w-5 text-red-400" />
        </div>
        <input
          type="text"
          value={url}
          onChange={handleChange}
          onPaste={handlePaste}
          placeholder="https://youtube.com/watch?v=..."
          className="w-full bg-white/5 border border-white/10 rounded-lg pl-11 pr-4 py-3 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-white/20 focus:bg-white/[0.07] transition-colors"
        />
        <AnimatePresence>
          {showUrlAnimation && (
            <motion.div
              className="absolute inset-0 rounded-lg pointer-events-none"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <motion.div
                className="absolute inset-0 rounded-lg"
                style={{
                  background: 'linear-gradient(90deg, rgba(34, 197, 94, 0.6), rgba(168, 85, 247, 0.6), rgba(59, 130, 246, 0.6), rgba(34, 197, 94, 0.6))',
                  backgroundSize: '300% 100%',
                  padding: '2px',
                  WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                  WebkitMaskComposite: 'xor',
                  maskComposite: 'exclude'
                }}
                animate={{
                  backgroundPosition: ['0% 0%', '100% 0%', '0% 0%']
                }}
                transition={{
                  duration: 2,
                  ease: 'linear'
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <AnimatePresence>
        {videoId && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="mt-2 inline-flex items-center bg-green-500/10 text-green-400 text-xs font-semibold px-2.5 py-1 rounded-md border border-green-500/20"
          >
            <Check className="h-3 w-3 mr-1" />
            ID: {videoId}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
