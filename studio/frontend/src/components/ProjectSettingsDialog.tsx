import { X } from 'lucide-react'
import type { StudioProject } from '../types'

interface Props {
  open: boolean
  project: StudioProject
  onChange: (project: StudioProject) => void
  onClose: () => void
}

export function ProjectSettingsDialog({ open, project, onChange, onClose }: Props) {
  if (!open) return null
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="project-settings-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 id="project-settings-title">Project settings</h2>
            <p>Names stored in pedal memory use plain ASCII characters.</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close project settings"><X size={18} /></button>
        </div>
        <div className="form-stack">
          <label className="field">
            <span>Project file name</span>
            <input value={project.name} maxLength={60} onChange={(event) => onChange({ ...project, name: event.target.value })} />
          </label>
          <label className="field">
            <span>Startup configuration name <em>{project.globalSettings.configName.length}/16</em></span>
            <input value={project.globalSettings.configName} maxLength={16} onChange={(event) => onChange({ ...project, globalSettings: { ...project.globalSettings, configName: event.target.value } })} />
          </label>
          <label className="check-row">
            <input type="checkbox" checked={project.globalSettings.realtimePassthrough} onChange={(event) => onChange({ ...project, globalSettings: { ...project.globalSettings, realtimePassthrough: event.target.checked } })} />
            <span><strong>Realtime passthrough</strong><small>Forward USB clock, start, and stop messages to the 5-pin MIDI output.</small></span>
          </label>
          <p className="field-note">The global MIDI channel is stored in pedal memory for compatibility, but each command carries its own channel.</p>
        </div>
        <div className="modal-actions">
          <button className="button primary" onClick={onClose}>Done</button>
        </div>
      </section>
    </div>
  )
}
