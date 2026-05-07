import { useState, useRef, useCallback } from 'react'
import { submitExport, getJob } from '../services/api'
import type { Job, ExportRequest, JobStatus } from '../types'

const POLL_INTERVAL = 3_000   // ms
const TERMINAL: JobStatus[] = ['ready', 'failed']

export function useJob() {
  const [job, setJob] = useState<Job | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const startPolling = useCallback((jobId: string) => {
    stopPolling()
    timerRef.current = setInterval(async () => {
      try {
        const updated = await getJob(jobId)
        setJob(updated)
        if (TERMINAL.includes(updated.status)) stopPolling()
      } catch {
        // transient network error — continue polling
      }
    }, POLL_INTERVAL)
  }, [stopPolling])

  const submit = useCallback(async (request: ExportRequest) => {
    setError(null)
    setJob(null)
    stopPolling()
    try {
      const created = await submitExport(request)
      setJob(created)
      if (!TERMINAL.includes(created.status)) {
        startPolling(created.id)
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Export request failed'
      setError(msg)
    }
  }, [startPolling, stopPolling])

  const reset = useCallback(() => {
    stopPolling()
    setJob(null)
    setError(null)
  }, [stopPolling])

  return { job, error, submit, reset }
}
