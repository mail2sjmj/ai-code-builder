import { useState } from 'react'
import appConfig from '@/config/app.config'
import { apiGet, apiPost } from '@/services/apiClient'
import { useCodeStore } from '@/store/codeStore'
import { useExecutionStore } from '@/store/executionStore'
import { useSessionStore } from '@/store/sessionStore'
import { toastError, toastSuccess } from '@/utils/toast'
import type { ExecutionJobResponse, ExecutionResult } from '@/types/api.types'

export function useCodeExecution() {
  const [isExecuting, setIsExecuting] = useState(false)
  const { sessionId } = useSessionStore()
  const { editedCode } = useCodeStore()
  const { setJobId, setStatus, setResults, setError, setSessionId } = useExecutionStore()

  const executeCode = async () => {
    if (!sessionId || !editedCode.trim()) return
    setIsExecuting(true)
    setStatus('queued')
    setSessionId(sessionId)

    try {
      const jobResponse = await apiPost<ExecutionJobResponse>('/execute', {
        session_id: sessionId,
        code: editedCode,
      })
      setJobId(jobResponse.job_id)
      setStatus('running')

      // Poll for result
      const { pollIntervalMs, maxPollAttempts } = appConfig.execution
      let attempts = 0

      const poll = async (): Promise<void> => {
        attempts++
        if (attempts > maxPollAttempts) {
          setError('Execution timed out waiting for result.')
          setIsExecuting(false)
          return
        }

        const result = await apiGet<ExecutionResult>(
          `/execute/${sessionId}/${jobResponse.job_id}`,
        )

        if (result.status === 'success') {
          setResults(result.preview_rows, result.preview_columns, result.execution_time_ms)
          toastSuccess('Code executed successfully.')
          setIsExecuting(false)
        } else if (result.status === 'error') {
          setError(result.error_message ?? 'Execution failed.')
          toastError(result.error_message ?? 'Execution failed.')
          setIsExecuting(false)
        } else {
          // Still running or queued — keep polling
          setTimeout(() => void poll(), pollIntervalMs)
        }
      }

      setTimeout(() => void poll(), pollIntervalMs)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to execute code.'
      setError(message)
      toastError(message)
      setIsExecuting(false)
    }
  }

  return { executeCode, isExecuting }
}
