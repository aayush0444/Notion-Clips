import { ContentSourceSelector } from "@/components/app/ContentSourceSelector"
import { ModeSelector } from "@/components/app/ModeSelector"
import { ProcessButton } from "@/components/app/ProcessButton"
import { useAppStore } from "@/lib/store"

interface WorkspaceControlsProps {
  sessionId: string | null
  setViewMode: (mode: 'extract' | 'synthesis') => void
  handleProcessingChange: (state: boolean) => void
  setProcessingStage: (stage: any) => void
}

export function WorkspaceControls({
  sessionId,
  setViewMode,
  handleProcessingChange,
  setProcessingStage,
}: WorkspaceControlsProps) {
  const { sourceType, url } = useAppStore()

  return (
    <div className="flex-1 min-w-0 space-y-7">
      <div className="py-2">
        <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#9B7FD4] border-b border-[#E8E0F0] pb-2">Workspace Controls</div>
      </div>

      <div className="min-w-0">
        <ContentSourceSelector />
      </div>

      {sourceType !== "study_session" && (
        <div className="min-w-0">
          <ModeSelector onViewModeChange={setViewMode} />
        </div>
      )}

      {sourceType !== "study_session" && (
        <div className="min-w-0 pt-2">
          <ProcessButton onProcessingChange={handleProcessingChange} onStageChange={setProcessingStage} />
        </div>
      )}
    </div>
  )
}
