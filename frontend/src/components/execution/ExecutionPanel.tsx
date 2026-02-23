import { Download, Loader2, Play, Wrench } from 'lucide-react'
import { useCodeExecution } from '@/hooks/useCodeExecution'
import { useDownload } from '@/hooks/useDownload'
import { useAutoFix } from '@/hooks/useAutoFix'
import { useCodeStore } from '@/store/codeStore'
import { useExecutionStore } from '@/store/executionStore'
import { useSessionStore } from '@/store/sessionStore'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { OutputPreviewTable } from './OutputPreviewTable'
import { formatDuration } from '@/utils/formatters'

export function ExecutionPanel() {
  const generatedCode = useCodeStore((s) => s.generatedCode)
  const editedCode = useCodeStore((s) => s.editedCode)
  const sessionId = useSessionStore((s) => s.sessionId)
  const { status, errorMessage, executionTimeMs } = useExecutionStore()
  const { executeCode, isExecuting } = useCodeExecution()
  const { downloadCsv, isDownloading } = useDownload()
  const { autoFix, isFixing } = useAutoFix()

  if (!generatedCode || !sessionId) return null

  const canRun = !isExecuting && !isFixing

  return (
    <div className="flex flex-col gap-4 rounded-xl border bg-card p-4 shadow-sm">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold">Execute Code</span>
          <StatusBadge status={status} />
          {status === 'success' && executionTimeMs != null && (
            <span className="text-xs text-muted-foreground">
              Completed in {formatDuration(executionTimeMs)}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => void executeCode()}
            disabled={!canRun}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isExecuting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {isExecuting ? 'Running…' : 'Run Code'}
          </button>

          {status === 'success' && (
            <button
              onClick={() => void downloadCsv()}
              disabled={isDownloading}
              className="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              {isDownloading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Download CSV
            </button>
          )}
        </div>
      </div>

      {/* Error display with Auto-fix */}
      {status === 'error' && errorMessage && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs font-medium text-destructive">Execution Error</p>
            <button
              onClick={() => void autoFix(sessionId, editedCode, errorMessage)}
              disabled={isFixing || isExecuting}
              className="flex items-center gap-1.5 rounded-md bg-destructive/10 px-3 py-1 text-xs font-medium text-destructive hover:bg-destructive/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isFixing ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Wrench className="h-3 w-3" />
              )}
              {isFixing ? 'Fixing…' : 'Auto-fix'}
            </button>
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-xs text-destructive">
            {errorMessage}
          </pre>
        </div>
      )}

      {/* Preview table */}
      <OutputPreviewTable />
    </div>
  )
}
