import type { MachineStatus } from '../types'
import { statusTone } from '../utils/format'

export function StatusBadge({ status }: { status: MachineStatus | string }) {
  const tone = statusTone(status)
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tone.badge}`}>
      <span className="relative flex h-2.5 w-2.5">
        {status === 'RUNNING' && (
          <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${tone.dot}`} />
        )}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${tone.dot}`} />
      </span>
      {tone.label}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: string }) {
  const tone =
    severity === 'CRITICAL'
      ? 'bg-red-500/15 text-red-300 ring-red-500/40'
      : severity === 'WARNING'
        ? 'bg-amber-500/15 text-amber-200 ring-amber-500/40'
        : 'bg-sky-500/15 text-sky-200 ring-sky-500/40'
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${tone}`}>{severity}</span>
}
