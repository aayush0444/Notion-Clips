"use client"
import { useAppStore } from '@/lib/store'
import { Mode } from '@/lib/types'
import { cn } from '@/lib/utils'

export function ModeSelector() {
  const { mode, setMode } = useAppStore()
  
  const modes: { id: Mode; label: string }[] = [
    { id: 'study', label: 'Study' },
    { id: 'work', label: 'Work' },
    { id: 'quick', label: 'Quick' }
  ]

  return (
    <div>
      <label className="block text-xs text-white/40 mb-3 uppercase tracking-wider">
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
                "flex-1 px-4 py-2.5 rounded-md text-sm transition-all",
                isActive 
                  ? m.id === 'study'
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    : m.id === 'work'
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      : "bg-green-500/20 text-green-300 border border-green-500/30"
                  : "text-white/50 hover:text-white/70 hover:bg-white/5"
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
    </div>
  )
}
