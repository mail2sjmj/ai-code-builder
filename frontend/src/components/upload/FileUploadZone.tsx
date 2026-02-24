import { useRef, useState, type DragEvent } from 'react'
import { CheckCircle2, Clock, FileSpreadsheet, UploadCloud } from 'lucide-react'
import { useFileUpload } from '@/hooks/useFileUpload'
import { validateFile } from '@/utils/fileValidation'
import { toastError } from '@/utils/toast'
import { cn } from '@/lib/utils'
import { FileMetadataCard } from './FileMetadataCard'
import { useSessionStore } from '@/store/sessionStore'

type UploadMode = 'file' | 'file-with-meta'

// ── Shared toggle switch ──────────────────────────────────────────────────────

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={cn(
        'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        checked ? 'bg-primary' : 'bg-input',
      )}
    >
      <span
        className={cn(
          'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform duration-200',
          checked ? 'translate-x-5' : 'translate-x-0',
        )}
      />
    </button>
  )
}

// ── Reusable drop zone box ────────────────────────────────────────────────────

type DropZoneStatus = 'idle' | 'waiting' | 'ready' | 'uploading'

function DropZoneBox({
  label,
  onFile,
  status = 'idle',
  uploadProgress = 0,
  selectedFile,
}: {
  label: string
  onFile: (file: File) => void
  status?: DropZoneStatus
  uploadProgress?: number
  selectedFile?: File | null
}) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const isDisabled = status === 'uploading'

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && !isDisabled) onFile(file)
  }

  return (
    <div className="flex flex-col gap-2">
      {label && <p className="text-sm font-semibold text-foreground">{label}</p>}

      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); if (!isDisabled) setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onClick={() => !isDisabled && inputRef.current?.click()}
        className={cn(
          'relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-all duration-200',
          isDragging
            ? 'scale-[1.01] border-primary bg-primary/5'
            : status === 'ready'
              ? 'border-green-500 bg-green-50 dark:bg-green-950/20'
              : status === 'waiting'
                ? 'border-amber-400 bg-amber-50 dark:bg-amber-950/20'
                : 'border-border hover:border-primary/50 hover:bg-muted/30',
          isDisabled && 'pointer-events-none opacity-70',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) onFile(file)
          }}
        />

        {status === 'uploading' ? (
          <div className="flex w-full max-w-xs flex-col items-center gap-2">
            <p className="text-sm text-muted-foreground">Uploading… {uploadProgress}%</p>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : selectedFile ? (
          <>
            {status === 'ready' ? (
              <CheckCircle2 className="h-10 w-10 text-green-600" />
            ) : status === 'waiting' ? (
              <Clock className="h-10 w-10 text-amber-500" />
            ) : (
              <FileSpreadsheet className="h-10 w-10 text-green-600" />
            )}
            <p className="max-w-full truncate text-sm font-medium text-foreground">
              {selectedFile.name}
            </p>
            {status === 'waiting' && (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                Waiting for meta file…
              </p>
            )}
            {status !== 'waiting' && (
              <p className="text-xs text-muted-foreground">Click or drop to replace</p>
            )}
          </>
        ) : (
          <>
            <UploadCloud
              className={cn('h-10 w-10', isDragging ? 'text-primary' : 'text-muted-foreground')}
            />
            <p className="text-center text-sm font-medium">
              Drop a CSV or XLSX file here
              <br />
              <span className="text-muted-foreground">or click to browse</span>
            </p>
            <p className="text-xs text-muted-foreground">Maximum file size: 50 MB</p>
          </>
        )}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function FileUploadZone() {
  const [uploadMode, setUploadMode] = useState<UploadMode>('file')

  // "Upload File with Meta" — header options
  const [metaOption, setMetaOption] = useState<'first-row-header' | 'header-position' | null>(null)
  const [headerPosition, setHeaderPosition] = useState('')

  // "Upload File" — optional separate metadata file
  const [wantMetadata, setWantMetadata] = useState(false)
  const [dataFile, setDataFile] = useState<File | null>(null)
  const [metaFile, setMetaFile] = useState<File | null>(null)

  const { uploadFile, isPending, uploadProgress } = useFileUpload()
  const hasSession = useSessionStore((s) => !!s.sessionId)

  const resolveHeaderRow = (): number | undefined => {
    if (uploadMode !== 'file-with-meta') return undefined
    if (metaOption === 'first-row-header') return 1
    if (metaOption === 'header-position') {
      const n = parseInt(headerPosition, 10)
      return Number.isFinite(n) && n >= 1 ? n : undefined
    }
    return undefined
  }

  // Called when the data file is dropped/selected
  const handleDataFile = (file: File) => {
    const validation = validateFile(file)
    if (!validation.valid) { toastError(validation.error ?? 'Invalid file.'); return }

    if (wantMetadata) {
      // Store and wait; if meta is already ready, process immediately
      setDataFile(file)
      if (metaFile) uploadFile({ file, metaFile })
    } else {
      uploadFile({ file, headerRow: resolveHeaderRow() })
    }
  }

  // Called when the meta file is dropped/selected
  const handleMetaFile = (file: File) => {
    const validation = validateFile(file)
    if (!validation.valid) { toastError(validation.error ?? 'Invalid file.'); return }

    setMetaFile(file)
    // If data file is already staged, both are ready — process now
    if (dataFile) uploadFile({ file: dataFile, metaFile: file })
  }

  // Derive zone visual status for the data drop zone
  const dataZoneStatus = (): DropZoneStatus => {
    if (isPending) return 'uploading'
    if (dataFile && !metaFile) return 'waiting'
    if (dataFile && metaFile) return 'ready'
    return 'idle'
  }

  return (
    <div className="space-y-4">
      {/* Uploaded file summary */}
      {hasSession && <FileMetadataCard />}

      {/* Upload mode radio buttons */}
      <div className="flex items-center gap-6">
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="radio"
            name="uploadMode"
            value="file-with-meta"
            checked={uploadMode === 'file-with-meta'}
            onChange={() => setUploadMode('file-with-meta')}
            className="h-4 w-4 accent-primary"
          />
          <span className="text-sm font-medium">Upload File with Meta</span>
        </label>

        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="radio"
            name="uploadMode"
            value="file"
            checked={uploadMode === 'file'}
            onChange={() => setUploadMode('file')}
            className="h-4 w-4 accent-primary"
          />
          <span className="text-sm font-medium">Upload File</span>
        </label>
      </div>

      {/* "Upload File with Meta" — header options */}
      {uploadMode === 'file-with-meta' && (
        <div className="flex flex-wrap items-center gap-6 rounded-lg border bg-muted/30 px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-foreground">First Row Header</span>
            <Toggle
              checked={metaOption === 'first-row-header'}
              onChange={() =>
                setMetaOption((prev) => (prev === 'first-row-header' ? null : 'first-row-header'))
              }
            />
          </div>

          <div className="h-5 w-px bg-border" />

          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-foreground">Header Record Position</span>
            <Toggle
              checked={metaOption === 'header-position'}
              onChange={() =>
                setMetaOption((prev) => (prev === 'header-position' ? null : 'header-position'))
              }
            />
            {metaOption === 'header-position' && (
              <input
                type="number"
                min={1}
                value={headerPosition}
                onChange={(e) => setHeaderPosition(e.target.value)}
                placeholder="Row #"
                className="w-20 rounded-md border bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            )}
          </div>
        </div>
      )}

      {/* "Upload File" — optional metadata toggle */}
      {uploadMode === 'file' && (
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-foreground">Want to upload Metadata?</span>
          <Toggle
            checked={wantMetadata}
            onChange={(v) => {
              setWantMetadata(v)
              setDataFile(null)
              setMetaFile(null)
            }}
          />
        </div>
      )}

      {/* Drop zone(s) */}
      {uploadMode === 'file' && wantMetadata ? (
        <div className="grid grid-cols-2 gap-4">
          <DropZoneBox
            label="File Upload"
            onFile={handleDataFile}
            status={dataZoneStatus()}
            uploadProgress={uploadProgress}
            selectedFile={dataFile}
          />
          <DropZoneBox
            label="Meta Upload"
            onFile={handleMetaFile}
            status={metaFile ? 'ready' : 'idle'}
            selectedFile={metaFile}
          />
        </div>
      ) : (
        <DropZoneBox
          label=""
          onFile={handleDataFile}
          status={isPending ? 'uploading' : 'idle'}
          uploadProgress={uploadProgress}
        />
      )}
    </div>
  )
}
