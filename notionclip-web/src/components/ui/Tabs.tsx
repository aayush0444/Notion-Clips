"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

export function Tabs({ tabs, activeTab, onChange, className }: { tabs: string[], activeTab: string, onChange: (t: string) => void, className?: string }) {
  return (
    <div className={cn("flex space-x-2 border-b border-border mb-4", className)}>
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={cn(
            "relative px-4 py-2 text-sm font-medium transition-colors outline-none",
            activeTab === tab ? "text-slate-900" : "text-muted hover:text-slate-700"
          )}
        >
          {tab}
          {activeTab === tab && (
            <motion.div
              layoutId="tab-indicator"
              className="absolute bottom-[-1px] left-0 right-0 h-[2px] bg-gradient-primary"
              initial={false}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          )}
        </button>
      ))}
    </div>
  )
}

export function TabContent({ children, isActive }: { children: React.ReactNode, isActive: boolean }) {
  return (
    <AnimatePresence mode="wait">
      {isActive && (
        <motion.div
          key="content"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
