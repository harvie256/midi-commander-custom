import { CheckCircle2, ChevronDown, CircleHelp, FileText, Power, RefreshCw, Upload, Usb } from 'lucide-react'
import { useState } from 'react'
import type { DeviceScan, JobState, StudioProject, ValidationResult } from '../types'

interface Props {
  project: StudioProject
  validation: ValidationResult
  devices: DeviceScan
  inputName: string
  outputName: string
  uploadJob: JobState | null
  onInputChange: (name: string) => void
  onOutputChange: (name: string) => void
  onRefresh: () => void
  onUpload: () => void
}

const TROUBLESHOOTING = [
  ['No input found', 'The configuration uploader needs the pedal in normal mode. Power-cycle without holding D or Bank Down, then refresh.'],
  ['Stuck erasing', 'Disconnect other STM MIDI devices, close MIDI utilities, and confirm the custom firmware is running. The Studio uploader stops after a timeout instead of hanging indefinitely.'],
  ['Blank display after firmware update', 'This is expected before the first custom configuration is uploaded. Stay in normal mode and upload from this screen.'],
]

const BUTTON_IDS = ['1', '2', '3', '4', 'A', 'B', 'C', 'D']
const FIELD_NAMES: Record<string, string> = {
  bankSelect: 'Bank select',
  channel: 'MIDI channel',
  configName: 'Configuration name',
  durationMs: 'Duration',
  largeName: 'Large name',
  number: 'MIDI number',
  offValue: 'Off value',
  onValue: 'On value',
  smallName: 'Small line',
  velocity: 'Velocity',
}

function issueLocation(path: string): string {
  if (path.startsWith('globalSettings.')) {
    return `Project settings · ${FIELD_NAMES[path.split('.').at(-1) || ''] || 'Setting'}`
  }
  const bankMatch = path.match(/^banks\.(\d+)/)
  if (!bankMatch) return 'Project structure'
  const parts = [`Bank ${Number(bankMatch[1]) + 1}`]
  const buttonMatch = path.match(/\.buttons\.(\d+)/)
  if (buttonMatch) parts.push(`Button ${BUTTON_IDS[Number(buttonMatch[1])] || Number(buttonMatch[1]) + 1}`)
  const commandMatch = path.match(/\.commands\.(\d+)/)
  if (commandMatch) parts.push(`Command ${Number(commandMatch[1]) + 1}`)
  const field = path.split('.').at(-1) || ''
  if (FIELD_NAMES[field]) parts.push(FIELD_NAMES[field])
  return parts.join(' · ')
}

export function DevicePage({
  project,
  validation,
  devices,
  inputName,
  outputName,
  uploadJob,
  onInputChange,
  onOutputChange,
  onRefresh,
  onUpload,
}: Props) {
  const [logOpen, setLogOpen] = useState(true)
  const errors = validation.issues.filter((issue) => issue.level === 'error').length
  const ready = Boolean(inputName && outputName && errors === 0 && uploadJob?.status !== 'running')
  const success = uploadJob?.status === 'completed'
  const buttonHelp = success
    ? 'Upload complete. The pedal has restarted.'
    : errors
      ? 'Fix the validation errors shown above before uploading.'
      : ready
        ? 'This replaces the current custom configuration.'
        : 'Connect a compatible MIDI device to enable upload.'

  return (
    <main className="operations-page">
      <section className="connection-steps">
        <Step number={1} icon={<Power size={25} />} title="Power on normally" text="Configuration upload uses normal mode, not DFU mode." />
        <Step number={2} icon={<Usb size={25} />} title="Connect USB" text="Use a USB data cable directly to your Mac." />
        <div className="setup-step device-select-step">
          <span className="step-number">3</span>
          <span className="step-icon"><RefreshCw size={25} /></span>
          <div className="step-content">
            <h2>Select MIDI device</h2>
            <div className="device-selectors">
              <label className="field"><span>Input</span><select value={inputName} onChange={(event) => onInputChange(event.target.value)}><option value="">Select input…</option>{devices.inputs.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
              <label className="field"><span>Output</span><select value={outputName} onChange={(event) => onOutputChange(event.target.value)}><option value="">Select output…</option>{devices.outputs.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
              <button className="button text-button" onClick={onRefresh}><RefreshCw size={17} /> Refresh</button>
            </div>
            {!devices.connected && <div className="device-empty"><Usb size={23} /><span>No compatible STM MIDI endpoints found.</span></div>}
          </div>
        </div>
      </section>

      <aside className="program-summary">
        <section className="summary-panel">
          <div className="panel-title"><Upload size={24} /><h1>Ready to program</h1></div>
          <dl className="summary-list">
            <div><dt>Project</dt><dd>{project.name}</dd></div>
            <div><dt>Configuration size</dt><dd>{validation.stats.contentSize.toLocaleString()} bytes</dd></div>
            <div><dt>Commands</dt><dd>{validation.stats.commandCount} configured</dd></div>
            <div><dt>Validation</dt><dd className={errors ? 'status-error' : 'status-ok'}><CheckCircle2 size={17} /> {errors ? `${errors} errors` : 'No errors'}</dd></div>
          </dl>
          {validation.issues.length > 0 ? <div className="validation-issues" role="alert" aria-label="Configuration validation issues">
            <h2>{errors ? 'Fix before upload' : 'Configuration notes'}</h2>
            <ul>{validation.issues.map((issue, index) => <li className={`validation-${issue.level}`} key={`${issue.path}-${index}`}><strong>{issueLocation(issue.path)}</strong><span>{issue.message}</span></li>)}</ul>
          </div> : null}
          {uploadJob?.status === 'running' && <div className="progress-track" aria-label={`Upload ${uploadJob.progress}% complete`}><span style={{ width: `${uploadJob.progress}%` }} /></div>}
          <button className="button primary wide" disabled={!ready} onClick={onUpload}><Upload size={18} /> {uploadJob?.status === 'running' ? 'Uploading…' : 'Upload configuration'}</button>
          <p className="button-help">{buttonHelp}</p>
        </section>
        <section className="troubleshooting">
          <div className="panel-title small"><CircleHelp size={19} /><h2>Troubleshooting</h2></div>
          {TROUBLESHOOTING.map(([title, text]) => <details key={title}><summary>{title}<ChevronDown size={16} /></summary><p>{text}</p></details>)}
        </section>
      </aside>

      <section className="log-panel">
        <button className="log-heading" onClick={() => setLogOpen((open) => !open)}><span><FileText size={19} /> Upload log</span><ChevronDown size={17} className={logOpen ? 'rotated' : ''} /></button>
        {logOpen && <div className={`log-body ${uploadJob ? '' : 'empty'}`}>
          {uploadJob ? uploadJob.logs.map((line, index) => <p key={`${index}-${line}`}>{line}</p>) : <><FileText size={24} /><span>No upload activity yet.</span></>}
        </div>}
      </section>
    </main>
  )
}

function Step({ number, icon, title, text }: { number: number; icon: React.ReactNode; title: string; text: string }) {
  return <div className="setup-step"><span className="step-number">{number}</span><span className="step-icon">{icon}</span><div className="step-content"><h2>{title}</h2><p>{text}</p></div></div>
}
