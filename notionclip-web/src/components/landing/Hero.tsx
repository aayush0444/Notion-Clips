"use client"

import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import Link from 'next/link'

export function Hero() {
  return (
    <div className="relative pt-32 pb-20 sm:pt-40 sm:pb-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Badge variant="secondary" className="mb-8 px-4 py-1.5 text-sm font-medium">
            AI-Powered Study and Work Notes
          </Badge>
          
          <h1 className="font-display text-5xl font-extrabold tracking-tight sm:text-7xl lg:text-[80px] leading-none mb-6">
            <span className="block text-white">Stop Watching.</span>
            <span className="block bg-gradient-primary bg-clip-text text-transparent mt-2">Start Knowing.</span>
          </h1>
          
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted sm:text-xl leading-relaxed">
            Paste any YouTube URL. Get structured notes pushed to your Notion workspace — study notes, work briefs, or quick summaries.
          </p>
          
          <div className="mt-10 flex flex-col items-center justify-center space-y-4">
            <Link href="/app">
              <Button variant="gradient" size="lg" className="px-10 py-6 text-lg tracking-wide rounded-[12px]">
                Get Started
              </Button>
            </Link>
            <p className="text-sm text-muted">
              No account required. Works with any YouTube video.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
