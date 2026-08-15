import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { AppHeader } from './components/AppHeader'
import { DevicePage } from './components/DevicePage'
import { EditorPage } from './components/EditorPage'
import { FirmwarePage } from './components/FirmwarePage'
import { ProjectSettingsDialog } from './components/ProjectSettingsDialog'
import { Toast } from './components/Toast'
import { useJob } from './hooks/useJob'
import { useStudioProject } from './hooks/useStudioProject'
import type { AppPage, DeviceScan, FirmwareStatus, MidiCommand, StudioProject } from './types'

const EMPTY_DEVICES: DeviceScan = {
  inputs: [], outputs: [], compatibleInputs: [], compatibleOutputs: [], connected: false,
}

const EMPTY_FIRMWARE: FirmwareStatus = {
  platform: 'Detecting platform…',
  installed: false,
  deviceDetected: false,
  internalFlashDetected: false,
  firmwareFile: 'generated-20220424-163714.dfu',
  firmwareExists: true,
  detail: 'Checking firmware tools…',
  dependencyInstallSupported: false,
  dependencyActionLabel: 'Install dfu-util',
  driverHint: null,
  driverHelpUrl: null,
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export default function App() {
  const { project, setProject, validation, lastSaved } = useStudioProject()
  const [page, setPage] = useState<AppPage>('editor')
  const [selectedBank, setSelectedBank] = useState(0)
  const [selectedButton, setSelectedButton] = useState(1)
  const [selectedCommand, setSelectedCommand] = useState(0)
  const [devices, setDevices] = useState<DeviceScan>(EMPTY_DEVICES)
  const [inputName, setInputName] = useState('')
  const [outputName, setOutputName] = useState('')
  const [firmware, setFirmware] = useState<FirmwareStatus>(EMPTY_FIRMWARE)
  const [uploadJobId, setUploadJobId] = useState<string | null>(null)
  const [firmwareJobId, setFirmwareJobId] = useState<string | null>(null)
  const [recoveryConfirmed, setRecoveryConfirmed] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'error' | 'info' } | null>(null)
  const csvInput = useRef<HTMLInputElement>(null)
  const projectInput = useRef<HTMLInputElement>(null)
  const uploadJob = useJob(uploadJobId)
  const firmwareJob = useJob(firmwareJobId)

  const show = (message: string, tone: 'success' | 'error' | 'info' = 'info') => setToast({ message, tone })

  const refreshDevices = async () => {
    try {
      const result = await api.scanDevices()
      setDevices(result)
      setInputName((current) => current && result.inputs.includes(current) ? current : result.compatibleInputs[0] || '')
      setOutputName((current) => current && result.outputs.includes(current) ? current : result.compatibleOutputs[0] || '')
    } catch (error) {
      show(error instanceof Error ? error.message : 'Could not scan MIDI devices.', 'error')
    }
  }

  const refreshFirmware = async () => {
    try {
      setFirmware(await api.firmwareStatus())
    } catch (error) {
      show(error instanceof Error ? error.message : 'Could not check DFU status.', 'error')
    }
  }

  useEffect(() => { void refreshDevices(); void refreshFirmware() }, [])

  useEffect(() => {
    if (uploadJob?.status === 'completed') show('Configuration uploaded. The pedal restarted successfully.', 'success')
    if (uploadJob?.status === 'failed') show(uploadJob.message, 'error')
  }, [uploadJob?.status])

  useEffect(() => {
    if (firmwareJob?.status === 'completed') {
      show(firmwareJob.kind === 'dependency-install' ? 'dfu-util installed.' : 'Firmware installed successfully.', 'success')
      void refreshFirmware()
    }
    if (firmwareJob?.status === 'failed') show(firmwareJob.message, 'error')
  }, [firmwareJob?.status])

  useEffect(() => {
    setSelectedButton((current) => Math.min(current, 7))
    setSelectedCommand(0)
  }, [selectedBank])

  if (!project) return <div className="loading-screen"><span className="loading-mark" />Loading MIDI Commander Studio…</div>

  const importCsv = async (file: File) => {
    try {
      const imported = await api.importCsv(file)
      setProject(imported)
      setSelectedBank(0); setSelectedButton(0); setSelectedCommand(0)
      show(`Imported ${file.name}.`, 'success')
    } catch (error) {
      show(error instanceof Error ? error.message : 'CSV import failed.', 'error')
    }
  }

  const importProject = async (file: File) => {
    try {
      const parsed = JSON.parse(await file.text()) as StudioProject
      if (parsed.schemaVersion !== 1 || !Array.isArray(parsed.banks)) throw new Error('This is not a MIDI Commander Studio project file.')
      const checked = await api.validateProject(parsed)
      if (checked.issues.some((issue) => issue.level === 'error')) throw new Error(checked.issues.find((issue) => issue.level === 'error')!.message)
      setProject(parsed)
      setSettingsOpen(false)
      show(`Opened ${file.name}.`, 'success')
    } catch (error) {
      show(error instanceof Error ? error.message : 'Project import failed.', 'error')
    }
  }

  const saveProject = () => {
    download(new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' }), `${project.name.replace(/[^a-z0-9]+/gi, '-').toLowerCase() || 'midi-commander'}.mcs.json`)
    show('Project file saved.', 'success')
  }

  const exportCsv = async () => {
    try {
      download(await api.exportCsv(project), `${project.name.replace(/[^a-z0-9]+/gi, '-').toLowerCase() || 'midi-commander'}.csv`)
      show('Compatible CSV exported.', 'success')
    } catch (error) {
      show(error instanceof Error ? error.message : 'CSV export failed.', 'error')
    }
  }

  const testCommand = async (command: MidiCommand) => {
    if (!outputName) return
    try {
      await api.testCommand(outputName, command)
      show('Test command sent.', 'success')
    } catch (error) {
      show(error instanceof Error ? error.message : 'Test command failed.', 'error')
    }
  }

  const startUpload = async () => {
    try {
      const result = await api.startUpload(project, inputName, outputName)
      setUploadJobId(result.jobId)
    } catch (error) {
      show(error instanceof Error ? error.message : 'Could not start upload.', 'error')
    }
  }

  const installDependency = async () => {
    try {
      const result = await api.installDfuUtil()
      setFirmwareJobId(result.jobId)
    } catch (error) {
      show(error instanceof Error ? error.message : 'Could not install dfu-util.', 'error')
    }
  }

  const installFirmware = async () => {
    try {
      const result = await api.installFirmware(recoveryConfirmed)
      setFirmwareJobId(result.jobId)
    } catch (error) {
      show(error instanceof Error ? error.message : 'Could not start firmware install.', 'error')
    }
  }

  const quit = async () => {
    try {
      await api.shutdown()
      show('Studio stopped. You can close this browser tab.', 'success')
    } catch {
      show('Studio is already stopped. You can close this tab.', 'info')
    }
  }

  const contextualRefresh = () => page === 'firmware' ? void refreshFirmware() : void refreshDevices()

  return <div className="app-shell">
    <AppHeader
      page={page}
      connected={devices.connected}
      onNavigate={setPage}
      onImportCsv={() => csvInput.current?.click()}
      onSaveProject={saveProject}
      onExportCsv={() => void exportCsv()}
      onUpload={() => setPage('device')}
      onRefresh={contextualRefresh}
      onQuit={() => void quit()}
    />
    {page === 'editor' && <EditorPage
      project={project}
      validation={validation}
      selectedBank={selectedBank}
      selectedButton={selectedButton}
      selectedCommand={selectedCommand}
      lastSaved={lastSaved}
      canTest={Boolean(outputName)}
      onProjectChange={setProject}
      onSelectBank={setSelectedBank}
      onSelectButton={(index) => { setSelectedButton(index); setSelectedCommand(0) }}
      onSelectCommand={setSelectedCommand}
      onOpenSettings={() => setSettingsOpen(true)}
      onTestCommand={(command) => void testCommand(command)}
    />}
    {page === 'device' && <DevicePage
      project={project}
      validation={validation}
      devices={devices}
      inputName={inputName}
      outputName={outputName}
      uploadJob={uploadJob}
      onInputChange={setInputName}
      onOutputChange={setOutputName}
      onRefresh={() => void refreshDevices()}
      onUpload={() => void startUpload()}
    />}
    {page === 'firmware' && <FirmwarePage
      status={firmware}
      job={firmwareJob}
      recoveryConfirmed={recoveryConfirmed}
      onRecoveryChange={setRecoveryConfirmed}
      onRefresh={() => void refreshFirmware()}
      onInstallDependency={() => void installDependency()}
      onInstallFirmware={() => void installFirmware()}
    />}
    <ProjectSettingsDialog open={settingsOpen} project={project} onChange={setProject} onClose={() => setSettingsOpen(false)} onImportProject={() => projectInput.current?.click()} />
    <input ref={csvInput} type="file" accept=".csv,text/csv" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void importCsv(file); event.target.value = '' }} />
    <input ref={projectInput} type="file" accept=".json,.mcs.json,application/json" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void importProject(file); event.target.value = '' }} />
    {toast && <Toast message={toast.message} tone={toast.tone} onClose={() => setToast(null)} />}
  </div>
}
