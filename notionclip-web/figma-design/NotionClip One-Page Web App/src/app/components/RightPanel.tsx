import { StudyOutput } from "./StudyOutput";
import { WorkOutput } from "./WorkOutput";
import { QuickOutput } from "./QuickOutput";
import { ChatInterface } from "./ChatInterface";
import { motion } from "motion/react";

interface RightPanelProps {
  mode: 'study' | 'work' | 'quick';
  hasProcessed: boolean;
  isProcessing: boolean;
}

export function RightPanel({ mode, hasProcessed, isProcessing }: RightPanelProps) {
  if (isProcessing) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            className="w-20 h-20 mx-auto mb-6 relative"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <svg className="w-full h-full" viewBox="0 0 100 100">
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="rgba(59, 130, 246, 0.8)" />
                  <stop offset="50%" stopColor="rgba(168, 85, 247, 0.8)" />
                  <stop offset="100%" stopColor="rgba(34, 197, 94, 0.8)" />
                </linearGradient>
              </defs>
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="url(#gradient)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray="60 200"
              />
            </svg>
          </motion.div>
          <motion.div
            initial={{ opacity: 0.5 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, repeat: Infinity, repeatType: "reverse" }}
            className="text-white/60 text-sm"
          >
            Processing video with AI...
          </motion.div>
        </div>
      </div>
    );
  }

  if (!hasProcessed) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-white/40 mb-2">No results yet</div>
          <div className="text-sm text-white/30">
            Enter a YouTube URL and click Process Video to generate AI notes
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto p-8">
        {mode === 'study' && <StudyOutput />}
        {mode === 'work' && <WorkOutput />}
        {mode === 'quick' && <QuickOutput />}
        
        <ChatInterface />
      </div>
    </div>
  );
}