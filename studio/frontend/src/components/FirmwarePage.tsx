import { Battery, Check, ChevronDown, Cpu, ExternalLink, FileWarning, PackageOpen, RefreshCw, ShieldAlert, Usb, Zap } from 'lucide-react'
import { useState } from 'react'
import type { FirmwareStatus, JobState } from '../types'

interface Props {
  status: FirmwareStatus
  job: JobState | null
  recoveryConfirmed: boolean
  onRecoveryChange: (confirmed: boolean) => void
  onRefresh: () => void
  onInstallDependency: () => void
  onInstallFirmware: () => void
}

export function FirmwarePage({
  status,
  job,
  recoveryConfirmed,
  onRecoveryChange,
  onRefresh,
  onInstallDependency,
  onInstallFirmware,
}: Props) {
  const [logOpen, setLogOpen] = useState(true)
  const running = job?.status === 'running'
  const ready = status.internalFlashDetected && status.firmwareExists && recoveryConfirmed && !running

  return (
    <main className="firmware-page">
      <section className="firmware-workflow">
        <div className="firmware-intro"><div className="firmware-title-row"><h1>Install custom firmware</h1><span className="platform-chip">{status.platform}</span></div><p>This replaces the pedal firmware. Your stock EEPROM settings are left untouched.</p></div>
        <FirmwareStep number={1} title="Prepare" active>
          <p className="check-line"><Check size={17} /> Keep a matching stock .dfu backup</p>
          <p className="check-line"><Check size={17} /> Use a USB data cable</p>
          {!status.installed && status.dependencyInstallSupported && <button className="button secondary dependency-button" disabled={running} onClick={onInstallDependency}><PackageOpen size={17} /> {status.dependencyActionLabel}</button>}
          {!status.installed && !status.dependencyInstallSupported && <p className="platform-note">Install dfu-util with your operating system package manager, then check again.</p>}
          {status.platform === 'Windows' && <p className="platform-note">Studio downloads a pinned official Windows build and verifies it before use. No executable is stored in the repository.</p>}
        </FirmwareStep>
        <FirmwareStep number={2} title="Enter DFU mode" active>
          <p>Power off. Hold <strong>D + Bank Down</strong> while powering on. LED 3 should light.</p>
        </FirmwareStep>
        <FirmwareStep number={3} title="Verify target" active={status.internalFlashDetected}>
          <div className="verify-grid"><span>Expected</span><code>0483:df11 · alt 0 · Internal Flash</code><span>Current</span><strong className={status.internalFlashDetected ? 'status-ok' : ''}>{status.detail}</strong></div>
          {status.driverHint && !status.internalFlashDetected && <p className="driver-hint">{status.driverHint} {status.driverHelpUrl && <a href={status.driverHelpUrl} target="_blank" rel="noreferrer">Open official Zadig site <ExternalLink size={12} /></a>}</p>}
          <button className="button text-button" onClick={onRefresh}><RefreshCw size={16} /> Check again</button>
        </FirmwareStep>
        <FirmwareStep number={4} title="Install" active={ready}>
          <div className="verify-grid"><span>Bundled file</span><code>{status.firmwareFile}</code><span>Start address</span><code>0x08003000</code></div>
          <label className="check-row compact-check"><input type="checkbox" checked={recoveryConfirmed} onChange={(event) => onRecoveryChange(event.target.checked)} /><span>I have a stock firmware recovery file.</span></label>
          {running && <div className="progress-track"><span style={{ width: `${job.progress}%` }} /></div>}
          <button className="button primary wide" disabled={!ready} onClick={onInstallFirmware}><Cpu size={18} /> {running ? 'Installing firmware…' : 'Install firmware'}</button>
        </FirmwareStep>
      </section>

      <aside className="safety-panel">
        <h2>Before you continue</h2>
        <SafetyItem icon={<Cpu />} title="Development firmware">This build is intended for testing and development.</SafetyItem>
        <SafetyItem icon={<Zap />} title="Expression inputs are not supported">Expression pedal and EXP jacks are not functional.</SafetyItem>
        <SafetyItem icon={<Battery />} title="Battery behavior is unverified">Battery life and charging behavior may be affected.</SafetyItem>
        <SafetyItem icon={<FileWarning />} title="Do not flash backup/dumped_firmware.bin">Only flash the bundled custom DFU from this workflow.</SafetyItem>
      </aside>

      <section className="log-panel firmware-log">
        <button className="log-heading" onClick={() => setLogOpen((open) => !open)}><span><ShieldAlert size={19} /> Firmware log</span><ChevronDown size={17} className={logOpen ? 'rotated' : ''} /></button>
        {logOpen && <div className={`log-body ${job ? '' : 'empty'}`}>{job ? job.logs.map((line, index) => <p key={`${index}-${line}`}>{line}</p>) : <><Usb size={24} /><span>Waiting for a DFU device.</span></>}</div>}
      </section>
    </main>
  )
}

function FirmwareStep({ number, title, active, children }: { number: number; title: string; active: boolean; children: React.ReactNode }) {
  return <div className={`firmware-step ${active ? 'active' : ''}`}><span className="firmware-step-number">{number}</span><div><h2>{title}</h2>{children}</div></div>
}

function SafetyItem({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return <div className="safety-item"><span>{icon}</span><div><h3>{title}</h3><p>{children}</p></div></div>
}
