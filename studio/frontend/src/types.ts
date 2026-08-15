export type CommandType = 'PC' | 'CC' | 'Note' | 'PB' | 'Start' | 'Stop'

export interface MidiCommand {
  id: string
  type: CommandType
  channel: number
  number: number
  onValue: number
  offValue: number
  suppressOff: boolean
  bankSelect: number
  bankSelectHighByte: boolean
  toggle: boolean
  velocity: number
  durationMs: number
}

export interface PedalButton {
  id: string
  label: string
  commands: MidiCommand[]
}

export interface Bank {
  number: number
  largeName: string
  smallName: string
  buttons: PedalButton[]
}

export interface StudioProject {
  schemaVersion: number
  name: string
  globalSettings: {
    configName: string
    realtimePassthrough: boolean
    midiChannel: number
  }
  banks: Bank[]
}

export interface ValidationIssue {
  level: 'error' | 'warning'
  path: string
  message: string
}

export interface ValidationResult {
  issues: ValidationIssue[]
  stats: {
    contentSize: number
    commandCount: number
  }
}

export interface DeviceScan {
  inputs: string[]
  outputs: string[]
  compatibleInputs: string[]
  compatibleOutputs: string[]
  connected: boolean
}

export interface FirmwareStatus {
  platform: string
  installed: boolean
  deviceDetected: boolean
  internalFlashDetected: boolean
  firmwareFile: string
  firmwareExists: boolean
  detail: string
  dependencyInstallSupported: boolean
  dependencyActionLabel: string
  driverHint: string | null
  driverHelpUrl: string | null
}

export interface JobState {
  id: string
  kind: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  logs: string[]
  result: Record<string, unknown> | null
  createdAt: string
}

export type AppPage = 'editor' | 'device' | 'firmware'
