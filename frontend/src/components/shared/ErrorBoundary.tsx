import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error) {
    console.error('[ErrorBoundary]', error)
  }

  render() {
    if (this.state.hasError) {
      const isDev = import.meta.env.DEV
      return (
        <div className="flex min-h-screen items-center justify-center bg-background p-8">
          <div className="max-w-lg rounded-lg border border-destructive/30 bg-destructive/5 p-6">
            <h1 className="text-lg font-semibold text-destructive">Something went wrong</h1>
            {isDev && this.state.error && (
              <pre className="mt-3 max-h-64 overflow-auto rounded bg-muted p-3 text-xs text-foreground">
                {this.state.error.stack ?? this.state.error.message}
              </pre>
            )}
            {!isDev && (
              <p className="mt-2 text-sm text-muted-foreground">
                An unexpected error occurred. Please refresh the page.
              </p>
            )}
            <button
              className="mt-4 rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
