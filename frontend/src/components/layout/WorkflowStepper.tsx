import { CheckCircle, Circle, Loader2 } from 'lucide-react'
import { useSessionStore } from '@/store/sessionStore'
import { cn } from '@/lib/utils'

const STEPS = [
  { id: 1, label: 'Upload' },
  { id: 2, label: 'Instruct' },
  { id: 3, label: 'Refine' },
  { id: 4, label: 'Generate' },
  { id: 5, label: 'Execute' },
] as const

export function WorkflowStepper() {
  const currentStep = useSessionStore((s) => s.currentStep)

  return (
    <nav className="flex items-center justify-center gap-0 py-4">
      {STEPS.map((step, idx) => {
        const isDone = step.id < currentStep
        const isActive = step.id === currentStep
        const isPending = step.id > currentStep

        return (
          <div key={step.id} className="flex items-center">
            {/* Connector line */}
            {idx > 0 && (
              <div
                className={cn(
                  'h-px w-12 transition-colors duration-300',
                  isDone ? 'bg-primary' : 'bg-border',
                )}
              />
            )}

            <div className="flex flex-col items-center gap-1">
              {isDone && <CheckCircle className="h-6 w-6 text-primary" />}
              {isActive && <Loader2 className="h-6 w-6 animate-spin text-primary" />}
              {isPending && <Circle className="h-6 w-6 text-muted-foreground" />}
              <span
                className={cn(
                  'text-xs font-medium transition-colors',
                  isDone && 'text-primary',
                  isActive && 'text-primary font-semibold',
                  isPending && 'text-muted-foreground',
                )}
              >
                {step.label}
              </span>
            </div>
          </div>
        )
      })}
    </nav>
  )
}
