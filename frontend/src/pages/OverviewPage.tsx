import { Link } from 'react-router-dom'
import { usePolling } from '../hooks/usePolling'
import type { Machine } from '../types'
import { formatDuration, formatPercent, formatScenario, formatTime, statusBorder } from '../utils/format'
import { Banner } from '../components/Banner'
import { KpiCard } from '../components/KpiCard'
import { MachineActions } from '../components/MachineActions'
import { StatusBadge } from '../components/StatusBadge'

export function OverviewPage() {
  const { data, error, loading, reload } = usePolling<Machine[]>('/api/machines', 2500)
  const machines = data ?? []
  const running = machines.filter((machine) => machine.status === 'RUNNING').length
  const faults = machines.filter((machine) => machine.status === 'FAULT').length
  const production = machines.reduce((sum, machine) => sum + machine.production_count, 0)
  const downtime = machines.reduce((sum, machine) => sum + machine.downtime_seconds, 0)

  return (
    <div className="space-y-5">
      {error && <Banner tone="error">{error}</Banner>}
      {loading && !data && <p className="text-sm text-slate-400">Loading machine data…</p>}
      {data && data.length === 0 && <Banner tone="info">No machines are configured in the simulator.</Banner>}
      {data && data.length > 0 && (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Running" value={`${running} / ${machines.length}`} hint="Machines currently producing" />
            <KpiCard label="Faults" value={String(faults)} hint="Reset is required before restart" />
            <KpiCard label="Production count" value={production.toLocaleString()} hint="Simulated items, all machines" />
            <KpiCard label="Downtime" value={formatDuration(downtime)} hint="Fault time plus stopped time" />
          </section>
          <section className="grid gap-4 xl:grid-cols-2">
            {machines.map((machine) => (
              <article key={machine.id} className={`rounded-xl border border-l-4 border-slate-800 bg-slate-900/80 p-5 ${statusBorder(machine.status)}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <Link to={`/machines/${machine.id}`} className="text-lg font-semibold text-white hover:text-sky-300">
                      {machine.name}
                    </Link>
                    <p className="mt-1 font-mono text-xs text-slate-400">
                      {machine.id} · {machine.machine_type}
                    </p>
                    <p className="mt-1 text-sm text-slate-400">{machine.description}</p>
                  </div>
                  <StatusBadge status={machine.status} />
                </div>
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <Sensor label="Temperature" value={`${machine.temperature.toFixed(1)} °C`} />
                  <Sensor label="Vibration" value={`${machine.vibration.toFixed(2)} mm/s`} />
                  <Sensor label="Motor current" value={`${machine.motor_current.toFixed(2)} A`} />
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-2 text-sm text-slate-300 sm:grid-cols-4">
                  <div>
                    <dt className="text-xs text-slate-500">Production</dt>
                    <dd>{machine.production_count.toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Downtime</dt>
                    <dd>{formatDuration(machine.downtime_seconds)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Simulated OEE</dt>
                    <dd>{formatPercent(machine.oee.oee)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Updated</dt>
                    <dd>{formatTime(machine.last_update)}</dd>
                  </div>
                </dl>
                <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                  <span>Scenario: {formatScenario(machine.active_scenario)}</span>
                  {machine.active_alarm_count > 0 && (
                    <span className="text-amber-300">{machine.active_alarm_count} active alarm{machine.active_alarm_count === 1 ? '' : 's'}</span>
                  )}
                  {machine.status === 'FAULT' && <span className="text-red-300">Reset the machine before starting it again.</span>}
                </div>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                  <MachineActions machineId={machine.id} machineName={machine.name} status={machine.status} onDone={reload} />
                  <Link to={`/machines/${machine.id}`} className="text-sm text-sky-300 hover:text-sky-200">
                    View details
                  </Link>
                </div>
              </article>
            ))}
          </section>
        </>
      )}
    </div>
  )
}

function Sensor({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-950/70 px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
    </div>
  )
}
