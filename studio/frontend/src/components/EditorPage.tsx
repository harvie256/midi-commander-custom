import { Copy, GripVertical, Play, Plus, Settings, Trash2 } from 'lucide-react'
import type { MidiCommand, StudioProject, ValidationResult } from '../types'

const COMMAND_NAMES: Record<MidiCommand['type'], string> = {
  CC: 'Control change',
  PC: 'Program change',
  Note: 'MIDI note',
  PB: 'Pitch bend',
  Start: 'Transport start',
  Stop: 'Transport stop',
}

const newCommand = (): MidiCommand => ({
  id: crypto.randomUUID().replaceAll('-', ''),
  type: 'CC',
  channel: 1,
  number: 0,
  onValue: 127,
  offValue: 0,
  suppressOff: false,
  bankSelect: 0,
  bankSelectHighByte: false,
  toggle: false,
  velocity: 100,
  durationMs: 0,
})

interface Props {
  project: StudioProject
  validation: ValidationResult
  selectedBank: number
  selectedButton: number
  selectedCommand: number
  lastSaved: Date | null
  canTest: boolean
  onProjectChange: (project: StudioProject) => void
  onSelectBank: (index: number) => void
  onSelectButton: (index: number) => void
  onSelectCommand: (index: number) => void
  onOpenSettings: () => void
  onTestCommand: (command: MidiCommand) => void
}

export function EditorPage({
  project,
  validation,
  selectedBank,
  selectedButton,
  selectedCommand,
  lastSaved,
  canTest,
  onProjectChange,
  onSelectBank,
  onSelectButton,
  onSelectCommand,
  onOpenSettings,
  onTestCommand,
}: Props) {
  const bank = project.banks[selectedBank]
  const button = bank.buttons[selectedButton]
  const errors = validation.issues.filter((issue) => issue.level === 'error').length
  const warnings = validation.issues.filter((issue) => issue.level === 'warning').length

  const updateBank = (changes: Partial<typeof bank>) => {
    const banks = project.banks.map((item, index) => index === selectedBank ? { ...item, ...changes } : item)
    onProjectChange({ ...project, banks })
  }

  const updateButton = (changes: Partial<typeof button>) => {
    const buttons = bank.buttons.map((item, index) => index === selectedButton ? { ...item, ...changes } : item)
    updateBank({ buttons })
  }

  const updateCommand = (index: number, changes: Partial<MidiCommand>) => {
    const commands = button.commands.map((item, commandIndex) => commandIndex === index ? { ...item, ...changes } : item)
    updateButton({ commands })
  }

  const removeCommand = (index: number) => {
    updateButton({ commands: button.commands.filter((_, commandIndex) => commandIndex !== index) })
    onSelectCommand(Math.max(0, Math.min(index - 1, button.commands.length - 2)))
  }

  const duplicateCommand = (index: number) => {
    if (button.commands.length >= 10) return
    const commands = [...button.commands]
    commands.splice(index + 1, 0, { ...commands[index], id: crypto.randomUUID().replaceAll('-', '') })
    updateButton({ commands })
    onSelectCommand(index + 1)
  }

  const moveCommand = (from: number, to: number) => {
    if (from === to) return
    const commands = [...button.commands]
    const [moved] = commands.splice(from, 1)
    commands.splice(to, 0, moved)
    updateButton({ commands })
    onSelectCommand(to)
  }

  return (
    <main className="editor-layout">
      <aside className="bank-rail" aria-label="Banks">
        <span className="rail-title">Banks</span>
        {project.banks.map((item, index) => (
          <button key={item.number} className={index === selectedBank ? 'active' : ''} onClick={() => onSelectBank(index)} aria-label={`Bank ${index + 1}`}>
            {index + 1}
          </button>
        ))}
        <span className="rail-count">{selectedBank + 1} of 8 banks</span>
      </aside>

      <section className="pedal-workspace">
        <div className="bank-fields">
          <label className="field">
            <span>Bank</span>
            <select value={selectedBank} onChange={(event) => onSelectBank(Number(event.target.value))}>
              {project.banks.map((item, index) => <option key={item.number} value={index}>Bank {index + 1} of 8</option>)}
            </select>
          </label>
          <label className="field">
            <span>Large name <em>{bank.largeName.length}/4</em></span>
            <input value={bank.largeName} maxLength={4} onChange={(event) => updateBank({ largeName: event.target.value.toUpperCase() })} />
          </label>
          <label className="field">
            <span>Small line <em>{bank.smallName.length}/8</em></span>
            <input value={bank.smallName} maxLength={8} onChange={(event) => updateBank({ smallName: event.target.value })} />
          </label>
        </div>

        <div className="pedal-shell" aria-label={`Bank ${selectedBank + 1} pedal layout`}>
          {bank.buttons.map((item, index) => (
            <button key={item.id} className={`footswitch ${selectedButton === index ? 'selected' : ''}`} onClick={() => onSelectButton(index)}>
              <span className="switch-id">{item.id}</span>
              <span className="switch-led" />
              <span className="switch-hardware"><span /></span>
              <span className="switch-label">{item.label || `Switch ${item.id}`}</span>
            </button>
          ))}
        </div>
        <p className="canvas-help">Click a switch to edit its actions. Commands run from top to bottom.</p>
      </section>

      <aside className="command-inspector">
        <div className="inspector-header">
          <div>
            <h1>Button {button.id} <span>·</span> {button.label || `Switch ${button.id}`}</h1>
            <label className="inline-name"><span>Button label</span><input value={button.label} maxLength={16} onChange={(event) => updateButton({ label: event.target.value })} /></label>
          </div>
          <button className="button secondary small" disabled={!canTest || !button.commands[selectedCommand]} onClick={() => button.commands[selectedCommand] && onTestCommand(button.commands[selectedCommand])}>
            <Play size={15} /> Test command
          </button>
        </div>
        <div className="command-heading"><span>Commands</span><small>executed in order</small></div>
        <div className="command-list">
          {button.commands.length === 0 ? (
            <div className="empty-commands"><p>No commands on this switch.</p><span>Add one to define what happens when you press it.</span></div>
          ) : button.commands.map((command, index) => (
            <CommandCard
              key={command.id}
              command={command}
              index={index}
              selected={index === selectedCommand}
              onSelect={() => onSelectCommand(index)}
              onUpdate={(changes) => updateCommand(index, changes)}
              onDuplicate={() => duplicateCommand(index)}
              onDelete={() => removeCommand(index)}
              onDrop={(from) => moveCommand(from, index)}
            />
          ))}
        </div>
        <button className="add-command" disabled={button.commands.length >= 10} onClick={() => {
          updateButton({ commands: [...button.commands, newCommand()] })
          onSelectCommand(button.commands.length)
        }}><Plus size={20} /> Add command</button>
        <p className="inspector-help"><GripVertical size={16} /> Drag commands to reorder. Up to 10 commands can run on one press.</p>
      </aside>

      <footer className="status-bar">
        <button onClick={onOpenSettings}><Settings size={17} /><span>Project: <strong>{project.name}</strong></span></button>
        <span>Autosave: On</span>
        <span>Last saved: {lastSaved ? lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Saving…'}</span>
        <span className={errors ? 'status-error' : 'status-ok'}>Validation: {errors} errors, {warnings} warnings</span>
      </footer>
    </main>
  )
}

interface CommandCardProps {
  command: MidiCommand
  index: number
  selected: boolean
  onSelect: () => void
  onUpdate: (changes: Partial<MidiCommand>) => void
  onDuplicate: () => void
  onDelete: () => void
  onDrop: (from: number) => void
}

function CommandCard({ command, index, selected, onSelect, onUpdate, onDuplicate, onDelete, onDrop }: CommandCardProps) {
  return (
    <article
      className={`command-card ${selected ? 'selected' : ''}`}
      onClick={onSelect}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault()
        onDrop(Number(event.dataTransfer.getData('text/plain')))
      }}
    >
      <div className="command-card-title">
        <button className="drag-handle" draggable onDragStart={(event) => event.dataTransfer.setData('text/plain', String(index))} aria-label={`Drag command ${index + 1}`}><GripVertical size={18} /></button>
        <span className="command-number">{index + 1}</span>
        <select className="command-type" value={command.type} onChange={(event) => onUpdate({ type: event.target.value as MidiCommand['type'] })} onClick={(event) => event.stopPropagation()} aria-label="Command type">
          {Object.entries(COMMAND_NAMES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <button className="icon-button" onClick={(event) => { event.stopPropagation(); onDuplicate() }} aria-label="Duplicate command"><Copy size={16} /></button>
        <button className="icon-button danger" onClick={(event) => { event.stopPropagation(); onDelete() }} aria-label="Delete command"><Trash2 size={16} /></button>
      </div>
      <div className="command-fields" onClick={(event) => event.stopPropagation()}>
        {!['Start', 'Stop'].includes(command.type) && <NumberField label="Channel" value={command.channel} min={1} max={16} onChange={(value) => onUpdate({ channel: value })} />}
        {command.type === 'CC' && <>
          <NumberField label="Controller" value={command.number} min={0} max={127} onChange={(value) => onUpdate({ number: value })} />
          <NumberField label="On value" value={command.onValue} min={0} max={127} onChange={(value) => onUpdate({ onValue: value })} />
          {!command.suppressOff && <NumberField label="Off value" value={command.offValue} min={0} max={127} onChange={(value) => onUpdate({ offValue: value })} />}
          <SelectField label="Behavior" value={command.toggle ? 'toggle' : 'momentary'} onChange={(value) => onUpdate({ toggle: value === 'toggle' })} options={[['momentary', 'Momentary'], ['toggle', 'Toggle']]} />
          <label className="mini-check"><input type="checkbox" checked={command.suppressOff} onChange={(event) => onUpdate({ suppressOff: event.target.checked, toggle: event.target.checked ? false : command.toggle })} /><span>Send press only</span></label>
        </>}
        {command.type === 'PC' && <>
          <NumberField label="Program" value={command.number} min={0} max={127} onChange={(value) => onUpdate({ number: value })} />
          <NumberField label="Bank select" value={command.bankSelect} min={0} max={16383} onChange={(value) => onUpdate({ bankSelect: value })} />
          <label className="mini-check"><input type="checkbox" checked={command.bankSelectHighByte} onChange={(event) => onUpdate({ bankSelectHighByte: event.target.checked })} /><span>Send MSB + LSB</span></label>
        </>}
        {command.type === 'Note' && <>
          <NumberField label="Note" value={command.number} min={0} max={127} onChange={(value) => onUpdate({ number: value })} />
          <NumberField label="Velocity" value={command.velocity} min={0} max={127} onChange={(value) => onUpdate({ velocity: value })} />
          <NumberField label="Duration ms" value={command.durationMs} min={0} max={1270} step={10} onChange={(value) => onUpdate({ durationMs: value })} />
          <SelectField label="Behavior" value={command.toggle ? 'toggle' : 'momentary'} onChange={(value) => onUpdate({ toggle: value === 'toggle' })} options={[['momentary', 'Momentary'], ['toggle', 'Toggle']]} />
        </>}
        {command.type === 'PB' && <>
          <NumberField label="Pitch" value={command.onValue} min={-8192} max={8191} onChange={(value) => onUpdate({ onValue: value })} />
          <NumberField label="Duration ms" value={command.durationMs} min={0} max={1270} step={10} onChange={(value) => onUpdate({ durationMs: value })} />
          <SelectField label="Behavior" value={command.toggle ? 'toggle' : 'momentary'} onChange={(value) => onUpdate({ toggle: value === 'toggle' })} options={[['momentary', 'Momentary'], ['toggle', 'Toggle']]} />
        </>}
        {['Start', 'Stop'].includes(command.type) && <p className="command-explainer">Sends the global MIDI {command.type.toLowerCase()} message when pressed.</p>}
      </div>
    </article>
  )

}

function NumberField({ label, value, min, max, step = 1, onChange }: { label: string; value: number; min: number; max: number; step?: number; onChange: (value: number) => void }) {
  const parseNumber = (raw: string) => Number.isFinite(Number(raw)) ? Number(raw) : 0
  return <label className="compact-field"><span>{label}</span><input type="number" value={value} min={min} max={max} step={step} onChange={(event) => onChange(parseNumber(event.target.value))} /></label>
}

function SelectField({ label, value, options, onChange }: { label: string; value: string; options: [string, string][]; onChange: (value: string) => void }) {
  return <label className="compact-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([optionValue, labelText]) => <option key={optionValue} value={optionValue}>{labelText}</option>)}</select></label>
}
