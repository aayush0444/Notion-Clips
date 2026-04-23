import { AnimatePresence, motion } from "framer-motion"
import { WorkspaceControls } from "./WorkspaceControls"
import { X } from "lucide-react"

interface WorkspaceModalProps {
  isOpen: boolean
  onClose: () => void
  sessionId: string | null
  setViewMode: (mode: 'extract' | 'synthesis') => void
  handleProcessingChange: (state: boolean) => void
  setProcessingStage: (stage: any) => void
}

export function WorkspaceModal({
  isOpen,
  onClose,
  sessionId,
  setViewMode,
  handleProcessingChange,
  setProcessingStage,
}: WorkspaceModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center sm:p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full h-full sm:h-auto sm:max-h-[90vh] sm:max-w-[480px] bg-white sm:rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          >
            <div className="flex items-center justify-end p-4 pb-0 z-10">
              <button 
                onClick={onClose}
                className="p-1.5 bg-[#F0EBF8] hover:bg-[#E4D9F5] rounded-full transition-colors text-[#5A4A72]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 sm:p-6 overflow-y-auto">
              <WorkspaceControls
                sessionId={sessionId}
                setViewMode={setViewMode}
                handleProcessingChange={(state) => {
                  handleProcessingChange(state)
                  if (state) onClose()
                }}
                setProcessingStage={setProcessingStage}
              />
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
