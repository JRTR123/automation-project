import { Link } from 'react-router-dom'
import { usePolling } from '../hooks/usePolling'
import type { Machine } from '../types'
import { formatDuration, formatPercent, formatTime } from '../utils/format'
import { Banner } from '../components/Banner'
import { MachineActions } from '../components/MachineActions'
import { StatusBadge } from '../components/StatusBadge'

export function MachinesPage() {
  const { data, error, loading, reload } = usePolling<Machine[]>('/api/machines', 2500)

  return (
    <div className="space-y-4">
      {error && <Banner tone="error">{error}</Banner>}
      {loading && !data && <p className="text-sm text-slate-400">Loading machines…</p>}
      {data && data.length === 0 && <Banner tone="info">No machines are configured.</Banner>}
      {data && data.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Machine</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Temperature</th>
                <th className="px-4 py-3">Vibration</th>
                <th className="px-4 py-3">Current</th>
                <th className="px-4 py-3">Production</th>
                <th className="px-4 py-3">Downtime</th>
                <th className="px-4 py-3">OEE</th>
                <th className="px-4 py-3">Updated</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((machine) => (
                <tr key={machine.id} className="border-t border-slate-800 bg-slate-950/40">
                  <td className="px-4 py-3">
                    <Link to={`/machines/${machine.id}`} className="font-medium text-sky-300 hover:text-sky-200">
                      {machine.name}
                    </Link>
                    <p className="font-mono text-xs text-slate-500">{machine.id}</p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={machine.status} />
                  </td>
                  <td className="px-4 py-3">{machine.temperature.toFixed(1)} °C</td>
                  <td className="px-4 py-3">{machine.vibration.toFixed(2)} mm/s</td>
                  <td className="px-4 py-3">{machine.motor_current.toFixed(2)} A</td>
                  <td className="px-4 py-3">{machine.production_count.toLocaleString()}</td>
                  <td className="px-4 py-3">{formatDuration(machine.downtime_seconds)}</td>
                  <td className="px-4 py-3">{formatPercent(machine.oee.oee)}</td>
                  <td className="px-4 py-3 text-slate-400">{formatTime(machine.last_update)}</td>
                  <td className="px-4 py-3">
                    <MachineActions machineId={machine.id} machineName={machine.name} status={machine.status} onDone={reload} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
