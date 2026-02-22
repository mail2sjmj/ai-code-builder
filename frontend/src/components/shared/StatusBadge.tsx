import { cn } from '@/lib/utils'

type Status = 'idle' | 'queued' | 'running' | 'success' | 'error' | 'refining' | 'generating'

const statusConfig: Record<Status, { label: string; className: string }> = {
  idle: { label: 'Idle', className: 'bg-gray-100 text-gray-600' },
  queued: { label: 'Queued', className: 'bg-yellow-100 text-yellow-700' },
  running: { label: 'Running', className: 'bg-blue-100 text-blue-700 animate-pulse' },
  success: { label: 'Success', className: 'bg-green-100 text-green-700' },
  error: { label: 'Error', className: 'bg-red-100 text-red-700' },
  refining: { label: 'Refining…', className: 'bg-purple-100 text-purple-700 animate-pulse' },
  generating: { label: 'Generating…', className: 'bg-indigo-100 text-indigo-700 animate-pulse' },
}

interface StatusBadgeProps {
  status: Status
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.idle
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  )
}
