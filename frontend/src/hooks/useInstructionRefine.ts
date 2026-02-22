import { useState } from 'react'
import appConfig from '@/config/app.config'
import { useInstructionStore } from '@/store/instructionStore'
import { useSessionStore } from '@/store/sessionStore'
import { parseSSEStream } from '@/utils/streamParser'
import { toastError, toastInfo } from '@/utils/toast'

export function useInstructionRefine() {
  const [isRefining, setIsRefining] = useState(false)
  const { sessionId } = useSessionStore()
  const { rawInstructions, appendRefinedChunk, resetRefined, setIsRefining: storeSetRefining } =
    useInstructionStore()
  const { advanceStep } = useSessionStore()

  const refine = async () => {
    if (!sessionId || !rawInstructions.trim()) return
    setIsRefining(true)
    storeSetRefining(true)
    resetRefined()
    toastInfo('Refining instructions…')

    try {
      const response = await fetch(
        `${appConfig.api.baseUrl}${appConfig.api.prefix}/instructions/refine`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            raw_instructions: rawInstructions,
          }),
        },
      )

      if (!response.ok) {
        const err = (await response.json()) as { message?: string }
        throw new Error(err.message ?? `HTTP ${response.status}`)
      }

      await parseSSEStream(
        response,
        appendRefinedChunk,
        () => {
          advanceStep()
          setIsRefining(false)
          storeSetRefining(false)
        },
        (error) => {
          toastError(error)
          setIsRefining(false)
          storeSetRefining(false)
        },
      )
    } catch (err) {
      toastError(err instanceof Error ? err.message : 'Failed to refine instructions.')
      setIsRefining(false)
      storeSetRefining(false)
    }
  }

  return { refine, isRefining }
}
