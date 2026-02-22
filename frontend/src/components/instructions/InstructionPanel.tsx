import { Loader2, Sparkles } from 'lucide-react'
import { useInstructionRefine } from '@/hooks/useInstructionRefine'
import { useInstructionStore } from '@/store/instructionStore'
import { useSessionStore } from '@/store/sessionStore'
import { RawInstructionBox } from './RawInstructionBox'
import { RefinedPromptBox } from './RefinedPromptBox'

export function InstructionPanel() {
  const { refine, isRefining } = useInstructionRefine()
  const rawInstructions = useInstructionStore((s) => s.rawInstructions)
  const sessionId = useSessionStore((s) => s.sessionId)

  const canRefine = !!sessionId && rawInstructions.trim().length >= 20 && !isRefining

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <RawInstructionBox />
        <RefinedPromptBox />
      </div>

      <div className="flex justify-center">
        <button
          onClick={() => void refine()}
          disabled={!canRefine}
          className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isRefining ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Refining…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Refine Instructions
            </>
          )}
        </button>
      </div>
    </div>
  )
}
