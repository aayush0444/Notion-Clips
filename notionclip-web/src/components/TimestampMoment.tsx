"use client"

import { Play } from 'lucide-react'

interface TimestampMomentProps {
  moment: string
  description: string
  onTimestampClick?: (moment: string) => void
}

export function TimestampMoment({
  moment,
  description,
  onTimestampClick,
}: TimestampMomentProps) {
  // Parse MM:SS or HH:MM:SS to seconds for YouTube playback
  const parseTimestamp = (ts: string): number => {
    const parts = ts.split(':').map(p => parseInt(p, 10))
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1] // MM:SS
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2] // HH:MM:SS
    }
    return 0
  }

  const seconds = parseTimestamp(moment)

  return (
    <div className="flex gap-3 items-start p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 hover:bg-blue-500/10 transition-colors group">
      {onTimestampClick && (
        <button
          onClick={() => onTimestampClick(moment)}
          className="flex-shrink-0 px-2 py-1 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded text-xs font-mono text-blue-300 transition-colors flex items-center gap-1"
          title={`Jump to ${moment}`}
        >
          <Play className="w-3 h-3" />
          {moment}
        </button>
      )}
      {!onTimestampClick && (
        <div className="flex-shrink-0 px-2.5 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded text-xs font-mono text-blue-300">
          {moment}
        </div>
      )}
      <p className="text-sm text-white/80 pt-0.5">{description}</p>
    </div>
  )
}
