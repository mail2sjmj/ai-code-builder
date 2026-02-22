import { FileSpreadsheet, X } from 'lucide-react'
import { useSessionStore } from '@/store/sessionStore'
import { formatBytes, formatRowCount } from '@/utils/formatters'

export function FileMetadataCard() {
  const { fileMetadata, reset } = useSessionStore()
  if (!fileMetadata) return null

  const MAX_COLS_SHOWN = 5
  const extraCols = fileMetadata.columns.length - MAX_COLS_SHOWN

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="mt-0.5 h-8 w-8 shrink-0 text-green-600" />
          <div>
            <p className="font-semibold">{fileMetadata.filename}</p>
            <p className="text-sm text-muted-foreground">
              {formatRowCount(fileMetadata.rowCount)} rows · {fileMetadata.columnCount} columns ·{' '}
              {formatBytes(fileMetadata.fileSizeBytes)}
            </p>
          </div>
        </div>
        <button
          onClick={reset}
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          title="Remove file"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {fileMetadata.columns.slice(0, MAX_COLS_SHOWN).map((col) => (
          <span
            key={col}
            className="rounded bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground"
          >
            {col}
          </span>
        ))}
        {extraCols > 0 && (
          <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            +{extraCols} more
          </span>
        )}
      </div>
    </div>
  )
}
