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
  
  const modes: { id: Mode; icon: string; title: string; subtitle: string }[] = [
    { id: 'study', icon: '📚', title: 'Study', subtitle: 'Deep notes' },
    { id: 'work', icon: '💼', title: 'Work', subtitle: 'Decisions & briefs' },
    { id: 'quick', icon: '⚡', title: 'Quick', subtitle: '2-min summary' }
  ]
  
  const handleViewModeChange = (newView: 'extract' | 'synthesis') => {
    setViewMode(newView)
    onViewModeChange?.(newView)
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2 mb-4 block">
          Mode
        </label>
        
        {/* View Mode Tabs */}
        <div className="flex gap-2 bg-card/80 p-1">
          <button
            onClick={() => handleViewModeChange('extract')}
            className={cn(
              "flex-1 rounded-xl px-3 py-3 text-[14px] font-semibold transition-all duration-200 shadow-sm",
              viewMode === 'extract'
                ? "bg-[#F5F2FD] border border-[#7A5BB5] text-[#7A5BB5] shadow-sm ring-1 ring-[#7A5BB5]/10"
                : "bg-white border border-[#E8E0F0] text-[#5D546C] hover:border-[#7A5BB5]/50 hover:text-[#7A5BB5]"
            )}
          >
            Extract
          </button>
          <button
            onClick={() => handleViewModeChange('synthesis')}
            className={cn(
              "flex-1 rounded-xl px-3 py-3 text-[14px] font-bold transition-all duration-200 shadow-sm",
              viewMode === 'synthesis'
                ? "bg-[#F5F2FD] border border-[#7A5BB5] text-[#7A5BB5] shadow-sm ring-1 ring-[#7A5BB5]/10"
                : "bg-white border border-[#E8E0F0] text-[#5D546C] hover:border-[#7A5BB5]/50 hover:text-[#7A5BB5]"
            )}
          >
            Synthesis
          </button>
        </div>
      </div>
      
      {/* Processing Modes (only show if extract view) */}
      {viewMode === 'extract' && (
      <div>
        <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2 mb-4 block">
          Processing Mode
        </label>
        <div className="grid grid-cols-3 gap-3">
          {modes.map(m => {
            const isActive = mode === m.id
            return (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={cn(
                  "flex flex-col items-start p-3 rounded-xl border text-left transition-all duration-200 group shadow-sm",
                  isActive 
                    ? "bg-[#F5F2FD] border-[#7A5BB5] shadow-sm ring-1 ring-[#7A5BB5]/10"
                    : "bg-white border-[#E8E0F0] hover:border-[#7A5BB5]/50 hover:bg-[#F9F8FF]"
                )}
              >
                <div className="text-[20px] mb-2">{m.icon}</div>
                <div className={cn("font-bold text-[14px] leading-tight", isActive ? "text-[#3D344D]" : "text-[#5D546C]")}>
                  {m.title}
                </div>
                <div className={cn("text-[11px] mt-1 leading-tight font-medium", isActive ? "text-[#7A5BB5]" : "text-[#9B7FD4]")}>
                  {m.subtitle}
                </div>
              </button>
            )
          })}
        </div>
      </div>
      )}
      
      {/* Synthesis Mode Info */}
      {viewMode === 'synthesis' && (
        <div className="rounded-xl border border-[#D9C2E8] bg-[#F1E8F6] p-4 shadow-sm">
          <p className="text-[13px] text-[#7A5BB5] leading-relaxed font-medium">
            🔗 Compare and synthesize insights across multiple sessions. Identify patterns, contradictions, and knowledge gaps.
          </p>
        </div>
      )}
    </div>
  )
}
