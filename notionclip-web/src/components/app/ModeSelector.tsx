"use client"
import { useState } from 'react'
import { useAppStore } from '@/lib/store'
import { Mode } from '@/lib/types'
import { cn } from '@/lib/utils'

interface ModeSelectorProps {
  onViewModeChange?: (view: 'extract' | 'synthesis') => void
}

export function ModeSelector({ onViewModeChange }: ModeSelectorProps = {}) {
  const { mode, setMode } = useAppStore()
  const [viewMode, setViewMode] = useState<'extract' | 'synthesis'>('extract')
  
  const modes: { id: Mode; label: string }[] = [
    { id: 'study', label: 'Study' },
    { id: 'work', label: 'Work' },
    { id: 'quick', label: 'Quick' }
  ]
  
  const handleViewModeChange = (newView: 'extract' | 'synthesis') => {
    setViewMode(newView)
    onViewModeChange?.(newView)
  }

  return (
    <div>
      <label className="block text-xs app-text-muted mb-3 uppercase tracking-wider">
        Mode
      </label>
      
      {/* View Mode Tabs */}
      <div className="flex gap-2 bg-card/80 p-1 rounded-lg border border-border mb-4">
        <button
          onClick={() => handleViewModeChange('extract')}
          className={cn(
            "flex-1 px-3 py-2 rounded-md text-sm transition-all duration-200",
            viewMode === 'extract'
              ? "bg-[#EDE6FA] text-[#3D2466] border border-[#CDBAEF]"
              : "text-foreground/55 hover:text-foreground/80 hover:bg-[#F0EBF8]"
          )}
        >
          Extract
        </button>
        <button
          onClick={() => handleViewModeChange('synthesis')}
          className={cn(
            "flex-1 px-3 py-2 rounded-md text-sm transition-all duration-200",
            viewMode === 'synthesis'
              ? "bg-[#F1E8F6] text-[#7A5BB5] border border-[#D9C2E8]"
              : "text-foreground/55 hover:text-foreground/80 hover:bg-[#F0EBF8]"
          )}
        >
          Synthesis
        </button>
      </div>
      
      {/* Processing Modes (only show if extract view) */}
      {viewMode === 'extract' && (
      <>
      <label className="block text-xs app-text-muted mb-2 uppercase tracking-wider">
        Processing Mode
      </label>
    <div className="flex gap-2 bg-card/80 p-1 rounded-lg border border-border">
        {modes.map(m => {
          const isActive = mode === m.id
          return (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                "flex-1 px-4 py-2.5 rounded-md text-sm transition-all duration-200",
                isActive 
                  ? m.id === 'study'
                    ? "bg-[#E9F0FB] text-[#2F4E77] border border-[#C8D9F2]"
                    : m.id === 'work'
                      ? "bg-[#F1E8F6] text-[#7A5BB5] border border-[#D9C2E8]"
                      : "bg-[#EAF4EC] text-[#4F7D58] border border-[#C7DFC9]"
                  : "text-foreground/55 hover:text-foreground/80 hover:bg-[#F0EBF8]"
              )}
            >
              {m.label}
            </button>
          )
        })}
      </div>
      <div className="mt-3 text-xs app-text-muted leading-relaxed">
        {mode === 'study' && 'Build deep study notes with core concepts, formulas, and exam-ready revision prompts.'}
        {mode === 'work' && 'Get a practical work brief with a clear verdict, decisions, and next actions.'}
        {mode === 'quick' && 'Capture the fastest high-signal summary with takeaways and useful follow-ups.'}
      </div>
      </>
      )}
      
      {/* Synthesis Mode Info */}
      {viewMode === 'synthesis' && (
        <div className="mt-3 p-3 rounded-lg bg-[#F1E8F6] border border-[#D9C2E8]">
          <p className="text-xs text-[#7A5BB5] leading-relaxed">
            🔗 Compare and synthesize insights across multiple sessions. Identify patterns, contradictions, and knowledge gaps.
          </p>
        </div>
      )}
    </div>
  )
}
