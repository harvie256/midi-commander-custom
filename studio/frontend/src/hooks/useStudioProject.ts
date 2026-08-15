import { useEffect, useState } from 'react'
import { api } from '../api'
import type { StudioProject, ValidationResult } from '../types'

const STORAGE_KEY = 'midi-commander-studio:project:v1'

function readStoredProject(): StudioProject | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StudioProject) : null
  } catch {
    return null
  }
}

export function useStudioProject() {
  const [project, setProject] = useState<StudioProject | null>(() => readStoredProject())
  const [validation, setValidation] = useState<ValidationResult>({
    issues: [],
    stats: { contentSize: 0, commandCount: 0 },
  })
  const [lastSaved, setLastSaved] = useState<Date | null>(null)

  useEffect(() => {
    if (project) return
    let cancelled = false
    api.starterProject().then((starter) => {
      if (!cancelled) setProject(starter)
    })
    return () => {
      cancelled = true
    }
  }, [project])

  useEffect(() => {
    if (!project) return
    const timeout = window.setTimeout(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(project))
      setLastSaved(new Date())
    }, 250)
    return () => window.clearTimeout(timeout)
  }, [project])

  useEffect(() => {
    if (!project) return
    const controller = new AbortController()
    const timeout = window.setTimeout(() => {
      api
        .validateProject(project, controller.signal)
        .then(setValidation)
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === 'AbortError') return
          setValidation({
            issues: [{ level: 'error', path: 'project', message: 'Validation service unavailable.' }],
            stats: { contentSize: 0, commandCount: 0 },
          })
        })
    }, 180)
    return () => {
      window.clearTimeout(timeout)
      controller.abort()
    }
  }, [project])

  return { project, setProject, validation, lastSaved }
}
