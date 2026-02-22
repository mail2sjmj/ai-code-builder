import { Code2 } from 'lucide-react'
import { useSessionStore } from '@/store/sessionStore'
import { truncateId } from '@/utils/formatters'

export function AppHeader() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const env = import.meta.env.MODE

  return (
    <header className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-2">
          <Code2 className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">AI Code Builder</span>
        </div>

        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {sessionId && (
            <span className="font-mono text-xs">
              Session: <span className="text-foreground">{truncateId(sessionId)}</span>
            </span>
          )}
          {env !== 'production' && (
            <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
              {env}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
