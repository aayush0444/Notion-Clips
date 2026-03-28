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
      <label className="block text-xs text-white/40 mb-3 uppercase tracking-wider">
        Mode
      </label>
      
      {/* View Mode Tabs */}
      <div className="flex gap-2 bg-white/5 p-1 rounded-lg border border-white/10 mb-4">
        <button
          onClick={() => handleViewModeChange('extract')}
          className={cn(
            "flex-1 px-3 py-2 rounded-md text-sm transition-all duration-200",
            viewMode === 'extract'
              ? "bg-blue-500/20 text-blue-200 border border-blue-500/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
              : "text-white/50 hover:text-white/80 hover:bg-white/5"
          )}
        >
          Extract
        </button>
        <button
          onClick={() => handleViewModeChange('synthesis')}
          className={cn(
            "flex-1 px-3 py-2 rounded-md text-sm transition-all duration-200",
            viewMode === 'synthesis'
              ? "bg-purple-500/20 text-purple-200 border border-purple-500/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
              : "text-white/50 hover:text-white/80 hover:bg-white/5"
          )}
        >
          Synthesis
        </button>
      </div>
      
      {/* Processing Modes (only show if extract view) */}
      {viewMode === 'extract' && (
      <>
      <label className="block text-xs text-white/40 mb-2 uppercase tracking-wider">
        Processing Mode
      </label>
    <div className="flex gap-2 bg-white/5 p-1 rounded-lg border border-white/10">
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
                    ? "bg-blue-500/20 text-blue-200 border border-blue-500/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                    : m.id === 'work'
                      ? "bg-purple-500/20 text-purple-200 border border-purple-500/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                      : "bg-green-500/20 text-green-200 border border-green-500/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                  : "text-white/50 hover:text-white/80 hover:bg-white/5"
              )}
            >
              {m.label}
            </button>
          )
        })}
      </div>
      <div className="mt-3 text-xs text-white/40 leading-relaxed">
        {mode === 'study' && 'Build deep study notes with core concepts, formulas, and exam-ready revision prompts.'}
        {mode === 'work' && 'Get a practical work brief with a clear verdict, decisions, and next actions.'}
        {mode === 'quick' && 'Capture the fastest high-signal summary with takeaways and useful follow-ups.'}
      </div>
      </>
      )}
      
      {/* Synthesis Mode Info */}
      {viewMode === 'synthesis' && (
        <div className="mt-3 p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
          <p className="text-xs text-purple-200 leading-relaxed">
            🔗 Compare and synthesize insights across multiple sessions. Identify patterns, contradictions, and knowledge gaps.
          </p>
        </div>
      )}
    </div>
  )
}
