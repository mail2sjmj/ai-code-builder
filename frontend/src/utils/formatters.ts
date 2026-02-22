/** Formatting utilities for display values. */

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const value = (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)
  return `${value} ${units[i]}`
}

export function formatRowCount(n: number): string {
  return n.toLocaleString()
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function truncateId(id: string, length = 8): string {
  return id.slice(0, length)
}
