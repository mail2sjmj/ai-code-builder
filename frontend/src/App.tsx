import { Toaster } from 'sonner'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppHeader } from '@/components/layout/AppHeader'
import { WorkflowStepper } from '@/components/layout/WorkflowStepper'
import { FileUploadZone } from '@/components/upload/FileUploadZone'
import { InstructionPanel } from '@/components/instructions/InstructionPanel'
import { CodeGenPanel } from '@/components/codegen/CodeGenPanel'
import { ExecutionPanel } from '@/components/execution/ExecutionPanel'
import { useSessionStore } from '@/store/sessionStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: { retry: 0 },
  },
})

function MainContent() {
  const { sessionId, currentStep } = useSessionStore()

  return (
    <main className="mx-auto max-w-7xl px-6 py-6 space-y-6">
      {/* Step 1: Upload */}
      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Step 1 — Upload Data
        </h2>
        <FileUploadZone />
      </section>

      {/* Steps 2+3: Instructions */}
      {sessionId && (
        <section className="transition-all duration-300">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Step 2 — Write & Refine Instructions
          </h2>
          <InstructionPanel />
        </section>
      )}

      {/* Step 4: Code Generation */}
      {currentStep >= 3 && (
        <section className="transition-all duration-300">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Step 3 — Generate Python Code
          </h2>
          <CodeGenPanel />
        </section>
      )}

      {/* Step 5: Execute */}
      {currentStep >= 4 && (
        <section className="transition-all duration-300">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Step 4 — Execute & Download
          </h2>
          <ExecutionPanel />
        </section>
      )}
    </main>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background">
        <AppHeader />
        <WorkflowStepper />
        <MainContent />
      </div>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  )
}
