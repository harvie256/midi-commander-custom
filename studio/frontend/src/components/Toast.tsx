import { AlertCircle, CheckCircle2, X } from 'lucide-react'

interface Props {
  message: string
  tone: 'success' | 'error' | 'info'
  onClose: () => void
}

export function Toast({ message, tone, onClose }: Props) {
  return <div className={`toast ${tone}`} role="status">
    {tone === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
    <span>{message}</span>
    <button onClick={onClose} aria-label="Dismiss message"><X size={16} /></button>
  </div>
}
