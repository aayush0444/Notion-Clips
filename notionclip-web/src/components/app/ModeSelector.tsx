"use client"
import { useAppStore } from '@/lib/store'
import { Mode } from '@/lib/types'
import { cn } from '@/lib/utils'

export function ModeSelector() {
  const { mode, setMode } = useAppStore()
  
  const modes: { id: Mode; label: string; desc: string }[] = [
    { id: 'study', label: 'Study', desc: "Formula sheets, timestamped facts, self-test questions" },
    { id: 'work', label: 'Work', desc: "Watch or Skip verdict, tools, decisions, next actions" },
    { id: 'quick', label: 'Quick', desc: "The gist in two minutes" }
  ]

  const currentDesc = modes.find(m => m.id === mode)?.desc

  return (
    <div className="w-full mb-8 flex flex-col items-center">
      <div className="flex space-x-2 p-1">
        {modes.map(m => {
          const isActive = mode === m.id
          return (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                "px-5 py-2 rounded-lg text-sm font-medium transition-colors outline-none",
                isActive 
                  ? "bg-white text-black" 
                  : "text-muted hover:text-white bg-white/5 hover:bg-white/10"
              )}
            >
              {m.label}
            </button>
          )
        })}
      </div>
      <p className="mt-3 text-sm text-muted h-5 transition-all">
        {currentDesc}
      </p>
    </div>
  )
}
