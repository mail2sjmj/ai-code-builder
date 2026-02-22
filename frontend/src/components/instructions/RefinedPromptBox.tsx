import { useState } from 'react'
import { Pencil, Check } from 'lucide-react'
import { useInstructionStore } from '@/store/instructionStore'
import { cn } from '@/lib/utils'

export function RefinedPromptBox() {
  const { refinedPrompt, isRefining, setRefinedPrompt } = useInstructionStore()
  const [isEditing, setIsEditing] = useState(false)

  const isEmpty = !refinedPrompt && !isRefining

  return (
    <div className="flex flex-1 flex-col gap-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-foreground">
          Refined Prompt <span className="font-normal text-muted-foreground">(AI-Structured)</span>
        </label>
        {refinedPrompt && !isRefining && (
          <button
            onClick={() => setIsEditing((v) => !v)}
            className="flex items-center gap-1 rounded px-2 py-0.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            {isEditing ? (
              <>
                <Check className="h-3 w-3" /> Done
              </>
            ) : (
              <>
                <Pencil className="h-3 w-3" /> Edit
              </>
            )}
          </button>
        )}
      </div>

      {isEmpty && !isRefining && (
        <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed bg-muted/20 p-6 min-h-[220px]">
          <p className="text-center text-sm text-muted-foreground">
            Enter your instructions and click{' '}
            <span className="font-medium text-foreground">Refine Instructions</span>
          </p>
        </div>
      )}

      {(refinedPrompt || isRefining) && (
        <>
          {isEditing ? (
            <textarea
              value={refinedPrompt}
              onChange={(e) => setRefinedPrompt(e.target.value)}
              className="flex-1 resize-y rounded-lg border bg-background p-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[220px]"
              spellCheck={false}
            />
          ) : (
            <div
              className={cn(
                'flex-1 overflow-auto rounded-lg border bg-muted/30 p-3 font-mono text-sm whitespace-pre-wrap min-h-[220px]',
                isRefining && 'border-primary/30',
              )}
            >
              {refinedPrompt}
              {isRefining && (
                <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-primary align-middle" />
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
