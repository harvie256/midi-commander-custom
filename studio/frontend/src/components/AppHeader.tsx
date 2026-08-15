import {
  Cpu,
  Download,
  FileUp,
  Pencil,
  Power,
  RefreshCw,
  Save,
  Upload,
  Usb,
} from 'lucide-react'
import type { AppPage } from '../types'

interface Props {
  page: AppPage
  connected: boolean
  onNavigate: (page: AppPage) => void
  onImportCsv: () => void
  onSaveProject: () => void
  onExportCsv: () => void
  onUpload: () => void
  onRefresh: () => void
  onQuit: () => void
}

export function AppHeader({
  page,
  connected,
  onNavigate,
  onImportCsv,
  onSaveProject,
  onExportCsv,
  onUpload,
  onRefresh,
  onQuit,
}: Props) {
  return (
    <header className="app-header">
      <button className="brand" onClick={() => onNavigate('editor')} aria-label="Open editor">
        MIDI Commander Studio
      </button>
      <nav className="primary-nav" aria-label="Main navigation">
        <button className={page === 'editor' ? 'active' : ''} onClick={() => onNavigate('editor')}>
          <Pencil size={18} /> Editor
        </button>
        <button className={page === 'device' ? 'active' : ''} onClick={() => onNavigate('device')}>
          <Usb size={18} /> Device
        </button>
        <button className={page === 'firmware' ? 'active' : ''} onClick={() => onNavigate('firmware')}>
          <Cpu size={18} /> Firmware
        </button>
      </nav>
      <div className="header-actions">
        <span className={`connection-state ${connected ? 'connected' : ''}`}>
          <span className="status-dot" />
          {connected ? 'MIDI device connected' : 'MIDI device not connected'}
        </span>
        {page === 'editor' ? (
          <>
            <button className="button secondary compact" onClick={onImportCsv}>
              <FileUp size={17} /> Import CSV
            </button>
            <button className="button secondary compact" onClick={onSaveProject}>
              <Save size={17} /> Save project
            </button>
            <button className="button secondary compact" onClick={onExportCsv}>
              <Download size={17} /> Export CSV
            </button>
            <button className="button primary compact" onClick={onUpload}>
              <Upload size={17} /> Upload to pedal
            </button>
          </>
        ) : (
          <button className="button secondary compact" onClick={onRefresh}>
            <RefreshCw size={17} /> Check again
          </button>
        )}
        <button className="icon-button" onClick={onQuit} aria-label="Quit MIDI Commander Studio" title="Quit Studio">
          <Power size={17} />
        </button>
      </div>
    </header>
  )
}
