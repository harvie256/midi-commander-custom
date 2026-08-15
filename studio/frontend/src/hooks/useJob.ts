import { useEffect, useState } from 'react'
import { api } from '../api'
import type { JobState } from '../types'

export function useJob(jobId: string | null, onComplete?: (job: JobState) => void) {
  const [job, setJob] = useState<JobState | null>(null)

  useEffect(() => {
    if (!jobId) {
      setJob(null)
      return
    }
    let active = true
    let timeout: number | undefined

    const poll = async () => {
      try {
        const next = await api.job(jobId)
        if (!active) return
        setJob(next)
        if (next.status === 'completed' || next.status === 'failed') {
          onComplete?.(next)
          return
        }
        timeout = window.setTimeout(poll, 500)
      } catch {
        if (active) timeout = window.setTimeout(poll, 1000)
      }
    }

    void poll()
    return () => {
      active = false
      if (timeout) window.clearTimeout(timeout)
    }
  }, [jobId, onComplete])

  return job
}
