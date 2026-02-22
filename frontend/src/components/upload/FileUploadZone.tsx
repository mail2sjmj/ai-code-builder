import { useRef, useState, type DragEvent } from 'react'
import { UploadCloud } from 'lucide-react'
import { useFileUpload } from '@/hooks/useFileUpload'
import { validateFile } from '@/utils/fileValidation'
import { toastError } from '@/utils/toast'
import { cn } from '@/lib/utils'
import { FileMetadataCard } from './FileMetadataCard'
import { useSessionStore } from '@/store/sessionStore'

export function FileUploadZone() {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const { uploadFile, isPending, uploadProgress } = useFileUpload()
  const hasSession = useSessionStore((s) => !!s.sessionId)

  const handleFile = (file: File) => {
    const validation = validateFile(file)
    if (!validation.valid) {
      toastError(validation.error ?? 'Invalid file.')
      return
    }
    uploadFile(file)
  }

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  if (hasSession) return <FileMetadataCard />

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={() => setIsDragging(false)}
      onClick={() => inputRef.current?.click()}
      className={cn(
        'relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 transition-all duration-200',
        isDragging ? 'border-primary bg-primary/5 scale-[1.01]' : 'border-border hover:border-primary/50 hover:bg-muted/30',
        isPending && 'pointer-events-none opacity-70',
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) handleFile(file)
        }}
      />

      <UploadCloud className={cn('h-12 w-12', isDragging ? 'text-primary' : 'text-muted-foreground')} />

      {isPending ? (
        <div className="flex w-full max-w-xs flex-col items-center gap-2">
          <p className="text-sm text-muted-foreground">Uploading… {uploadProgress}%</p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      ) : (
        <>
          <p className="text-center text-sm font-medium">
            Drop your CSV or XLSX file here
            <br />
            <span className="text-muted-foreground">or click to browse</span>
          </p>
          <p className="text-xs text-muted-foreground">Maximum file size: 50 MB</p>
        </>
      )}
    </div>
  )
}
