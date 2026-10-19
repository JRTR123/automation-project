import type { MachineStatus, Severity } from '../types'

export function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainder = seconds % 60
  if (hours > 0) return `${hours}h ${minutes}m ${remainder}s`
  if (minutes > 0) return `${minutes}m ${remainder}s`
  return `${remainder}s`
}

export function formatPercent(fraction: number): string {
  if (!Number.isFinite(fraction)) return '0.0%'
  return `${(fraction * 100).toFixed(1)}%`
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

export function formatClock(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatScenario(scenario: string | null): string {
  if (!scenario) return 'None'
  const labels: Record<string, string> = {
    high_temperature: 'High temperature',
    excessive_vibration: 'Excessive vibration',
    motor_overload: 'Motor overload',
    machine_fault: 'Machine fault',
    idle: 'Idle operation',
  }
  return labels[scenario] ?? scenario
}

export function statusTone(status: string): { badge: string; dot: string; label: string } {
  switch (status) {
    case 'RUNNING':
      return {
        badge: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40',
        dot: 'bg-emerald-400',
        label: 'Running',
      }
    case 'IDLE':
      return {
        badge: 'bg-sky-500/15 text-sky-300 ring-sky-500/40',
        dot: 'bg-sky-400',
        label: 'Idle',
      }
    case 'STOPPED':
      return {
        badge: 'bg-slate-500/20 text-slate-300 ring-slate-500/40',
        dot: 'bg-slate-400',
        label: 'Stopped',
      }
    case 'FAULT':
      return {
        badge: 'bg-red-500/15 text-red-300 ring-red-500/40',
        dot: 'bg-red-400',
        label: 'Fault',
      }
    default:
      return {
        badge: 'bg-slate-500/20 text-slate-300 ring-slate-500/40',
        dot: 'bg-slate-400',
        label: status,
      }
  }
}

export function severityTone(severity: Severity | string): string {
  switch (severity) {
    case 'CRITICAL':
      return 'bg-red-500/15 text-red-300 ring-red-500/40'
    case 'WARNING':
      return 'bg-amber-500/15 text-amber-200 ring-amber-500/40'
    default:
      return 'bg-sky-500/15 text-sky-200 ring-sky-500/40'
  }
}

export function statusBorder(status: MachineStatus): string {
  switch (status) {
    case 'RUNNING':
      return 'border-l-emerald-400'
    case 'IDLE':
      return 'border-l-sky-400'
    case 'STOPPED':
      return 'border-l-slate-500'
    case 'FAULT':
      return 'border-l-red-500'
    default:
      return 'border-l-slate-500'
  }
}
