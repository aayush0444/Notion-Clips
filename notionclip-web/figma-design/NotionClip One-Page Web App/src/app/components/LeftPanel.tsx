import { Youtube } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";

interface LeftPanelProps {
  url: string;
  onUrlChange: (url: string) => void;
  mode: 'study' | 'work' | 'quick';
  onModeChange: (mode: 'study' | 'work' | 'quick') => void;
  onProcess: () => void;
  isProcessing: boolean;
  stats: {
    processingTime?: string;
    videoLength?: string;
    wordCount?: number;
    keyPointsCount?: number;
  } | null;
  isNotionConnected: boolean;
  onSaveToNotion: () => void;
  hasProcessed: boolean;
}

export function LeftPanel({ 
  url, 
  onUrlChange, 
  mode, 
  onModeChange, 
  onProcess,
  isProcessing,
  stats,
  isNotionConnected,
  onSaveToNotion,
  hasProcessed
}: LeftPanelProps) {
  const [showUrlAnimation, setShowUrlAnimation] = useState(false);

  const handleUrlPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    setShowUrlAnimation(true);
    setTimeout(() => setShowUrlAnimation(false), 2000);
  };

  return (
    <div className="w-[400px] border-r border-white/5 p-8 flex flex-col">
      <div className="flex-1 space-y-6">
        <div>
          <label className="block text-xs text-white/40 mb-2 uppercase tracking-wider">
            Video URL
          </label>
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-red-400">
              <Youtube className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => onUrlChange(e.target.value)}
              onPaste={handleUrlPaste}
              placeholder="https://youtube.com/watch?v=..."
              className="w-full bg-white/5 border border-white/10 rounded-lg px-11 py-3 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-white/20 focus:bg-white/[0.07] transition-colors relative z-10"
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
        </div>

        <div>
          <label className="block text-xs text-white/40 mb-3 uppercase tracking-wider">
            Processing Mode
          </label>
          <div className="flex gap-2 bg-white/5 p-1 rounded-lg border border-white/10">
            <button
              onClick={() => onModeChange('study')}
              className={`
                flex-1 px-4 py-2.5 rounded-md text-sm transition-all
                ${mode === 'study' 
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' 
                  : 'text-white/50 hover:text-white/70 hover:bg-white/5'
                }
              `}
            >
              Study
            </button>
            <button
              onClick={() => onModeChange('work')}
              className={`
                flex-1 px-4 py-2.5 rounded-md text-sm transition-all
                ${mode === 'work' 
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                  : 'text-white/50 hover:text-white/70 hover:bg-white/5'
                }
              `}
            >
              Work
            </button>
            <button
              onClick={() => onModeChange('quick')}
              className={`
                flex-1 px-4 py-2.5 rounded-md text-sm transition-all
                ${mode === 'quick' 
                  ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                  : 'text-white/50 hover:text-white/70 hover:bg-white/5'
                }
              `}
            >
              Quick
            </button>
          </div>
          
          <div className="mt-3 text-xs text-white/40 leading-relaxed">
            {mode === 'study' && 'Extracts formulas, key facts, and self-test questions from lectures'}
            {mode === 'work' && 'Generates watch/skip verdict, tools mentioned, and action items'}
            {mode === 'quick' && 'Provides a concise summary and key takeaways'}
          </div>
        </div>

        <button
          onClick={onProcess}
          disabled={!url || isProcessing}
          className="w-full bg-white text-black py-3.5 rounded-lg hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm font-medium"
        >
          {isProcessing ? 'Processing...' : 'Process Video'}
        </button>

        {hasProcessed && isNotionConnected && (
          <motion.button
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={onSaveToNotion}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-3.5 rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all text-sm font-medium shadow-lg shadow-blue-500/20"
          >
            Save to Notion
          </motion.button>
        )}

        {stats && (
          <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/5">
            <div className="bg-white/5 rounded-lg p-3 border border-white/10">
              <div className="text-xs text-white/40 mb-1">Processing Time</div>
              <div className="text-sm text-white/90">{stats.processingTime}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-3 border border-white/10">
              <div className="text-xs text-white/40 mb-1">Video Length</div>
              <div className="text-sm text-white/90">{stats.videoLength}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-3 border border-white/10">
              <div className="text-xs text-white/40 mb-1">Word Count</div>
              <div className="text-sm text-white/90">{stats.wordCount?.toLocaleString()}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-3 border border-white/10">
              <div className="text-xs text-white/40 mb-1">Key Points</div>
              <div className="text-sm text-white/90">{stats.keyPointsCount}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}