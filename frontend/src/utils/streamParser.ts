/**
 * Parse a Server-Sent Events (SSE) streaming response.
 * Handles partial lines and buffers incomplete chunks.
 */
export async function parseSSEStream(
  response: Response,
  onChunk: (chunk: string) => void,
  onDone: () => void,
  onError?: (error: string) => void,
): Promise<void> {
  if (!response.body) {
    throw new Error('Response body is null — SSE stream not available.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Process complete lines (SSE events end with \n\n)
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? '' // keep the last incomplete line

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || trimmed.startsWith(':')) continue // empty or comment

        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6)
          try {
            const parsed = JSON.parse(jsonStr) as Record<string, unknown>
            if (parsed.done === true) {
              onDone()
              return
            }
            if (typeof parsed.chunk === 'string') {
              onChunk(parsed.chunk)
            }
            if (typeof parsed.error === 'string') {
              onError?.(parsed.error)
              return
            }
          } catch {
            // Ignore malformed SSE data lines
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }

  // Stream ended without a done sentinel
  onDone()
}
