import type {
  DeviceScan,
  FirmwareStatus,
  JobState,
  MidiCommand,
  StudioProject,
  ValidationResult,
} from './types'

async function responseError(response: Response): Promise<Error> {
  try {
    const body = await response.json()
    return new Error(body.detail || `Request failed (${response.status})`)
  } catch {
    return new Error(`Request failed (${response.status})`)
  }
}

async function json<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) throw await responseError(response)
  return response.json() as Promise<T>
}

const postJson = <T>(url: string, body: unknown) =>
  json<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export const api = {
  starterProject: () => json<StudioProject>('/api/project/starter'),
  validateProject: (project: StudioProject, signal?: AbortSignal) =>
    json<ValidationResult>('/api/project/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project),
      signal,
    }),
  scanDevices: () => json<DeviceScan>('/api/devices'),
  firmwareStatus: () => json<FirmwareStatus>('/api/firmware/status'),
  job: (id: string) => json<JobState>(`/api/jobs/${id}`),
  startUpload: (project: StudioProject, inputName: string, outputName: string) =>
    postJson<{ jobId: string }>('/api/upload/start', { project, inputName, outputName }),
  testCommand: (outputName: string, command: MidiCommand) =>
    postJson<{ sent: boolean }>('/api/commands/test', { outputName, command }),
  installDfuUtil: () => postJson<{ jobId: string }>('/api/firmware/install-dfu-util', {}),
  installFirmware: (recoveryConfirmed: boolean) =>
    postJson<{ jobId: string }>('/api/firmware/install', { recoveryConfirmed }),
  shutdown: () => postJson<{ stopping: boolean }>('/api/shutdown', {}),
  importCsv: async (file: File) => {
    const data = new FormData()
    data.append('file', file)
    const response = await fetch('/api/csv/import', { method: 'POST', body: data })
    if (!response.ok) throw await responseError(response)
    return response.json() as Promise<StudioProject>
  },
  exportCsv: async (project: StudioProject) => {
    const response = await fetch('/api/csv/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project),
    })
    if (!response.ok) throw await responseError(response)
    return response.blob()
  },
}
