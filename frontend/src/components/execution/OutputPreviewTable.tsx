import { useExecutionStore } from '@/store/executionStore'
import { formatRowCount } from '@/utils/formatters'
import appConfig from '@/config/app.config'

export function OutputPreviewTable() {
  const { previewRows, previewColumns, status } = useExecutionStore()

  if (status !== 'success' && status !== 'running') return null

  if (status === 'running') {
    return (
      <div className="rounded-lg border bg-muted/20 p-6 text-center text-sm text-muted-foreground animate-pulse">
        Executing code…
      </div>
    )
  }

  if (previewRows.length === 0) {
    return (
      <div className="rounded-lg border bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No output rows to preview.
      </div>
    )
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-muted">
            <tr>
              {previewColumns.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap border-b px-3 py-2 text-left font-medium text-muted-foreground"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {previewRows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
                {previewColumns.map((col) => (
                  <td key={col} className="whitespace-nowrap px-3 py-1.5 font-mono text-xs">
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t bg-muted/10 px-3 py-1.5 text-xs text-muted-foreground">
        Showing {formatRowCount(previewRows.length)} of up to {appConfig.preview.rowCount} preview rows
      </div>
    </div>
  )
}
