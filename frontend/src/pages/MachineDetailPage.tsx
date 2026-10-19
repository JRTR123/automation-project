import { Link, useParams } from 'react-router-dom'
import { acknowledgeAlarm } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import type { History } from '../types'
import { formatDuration, formatPercent, formatScenario, formatTime } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { Banner } from '../components/Banner'
import { KpiCard, OeeBar } from '../components/KpiCard'
import { MachineActions } from '../components/MachineActions'
import { ScenarioPanel } from '../components/ScenarioPanel'
import { SensorChart } from '../components/SensorChart'
import { SeverityBadge, StatusBadge } from '../components/StatusBadge'

export function MachineDetailPage() {
  const { machineId = '' } = useParams()
  const { push } = useToast()
  const { data, error, loading, reload } = usePolling<History>(machineId ? `/api/machines/${machineId}/history?limit=80` : null, 2500)
  const machine = data?.machine

  async function acknowledge(alarmId: number) {
    try {
      await acknowledgeAlarm(alarmId)
      push('Alarm acknowledged. The machine state was not changed.', 'success')
      reload()
    } catch (caught) {
      push(caught instanceof Error ? caught.message : 'Could not acknowledge the alarm', 'error')
    }
  }

  if (!machineId) return <Banner tone="error">Missing machine id.</Banner>

  return (
    <div className="space-y-5">
      <Link to="/machines" className="text-sm text-sky-300 hover:text-sky-200">
        Back to machines
      </Link>
      {error && <Banner tone="error">{error}</Banner>}
      {loading && !data && <p className="text-sm text-slate-400">Loading machine history…</p>}
      {machine && data && (
        <>
          <section className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h3 className="text-2xl font-semibold text-white">{machine.name}</h3>
                <StatusBadge status={machine.status} />
              </div>
              <p className="mt-1 font-mono text-xs text-slate-400">
                {machine.id} · {machine.machine_type}
              </p>
              <p className="mt-2 max-w-2xl text-sm text-slate-300">{machine.description}</p>
              <p className="mt-2 text-sm text-slate-400">Active scenario: {formatScenario(machine.active_scenario)}</p>
            </div>
            <MachineActions machineId={machine.id} machineName={machine.name} status={machine.status} onDone={reload} />
          </section>

          {machine.status === 'FAULT' && (
            <Banner tone="error">
              This machine is in FAULT. Acknowledging the alarm only records that an operator has seen it. Use Reset to clear the fault and return the machine to IDLE, then Start to run it again.
            </Banner>
          )}

          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Temperature" value={`${machine.temperature.toFixed(1)} °C`} hint={`Warning ${machine.temp_warning} / critical ${machine.temp_critical}`} />
            <KpiCard label="Vibration" value={`${machine.vibration.toFixed(2)} mm/s`} hint={`Warning ${machine.vib_warning} / critical ${machine.vib_critical}`} />
            <KpiCard label="Motor current" value={`${machine.motor_current.toFixed(2)} A`} hint={`Warning ${machine.current_warning} / critical ${machine.current_critical}`} />
            <KpiCard label="Production" value={machine.production_count.toLocaleString()} hint={`${machine.good_count} good · ${machine.defect_count} defective`} />
          </section>

          <section className="grid gap-4 xl:grid-cols-3">
            <SensorChart title="Temperature" data={data.readings} dataKey="temperature" color="#fbbf24" unit="°C" warning={machine.temp_warning} critical={machine.temp_critical} />
            <SensorChart title="Vibration" data={data.readings} dataKey="vibration" color="#38bdf8" unit="mm/s" warning={machine.vib_warning} critical={machine.vib_critical} />
            <SensorChart title="Motor current" data={data.readings} dataKey="motor_current" color="#a78bfa" unit="A" warning={machine.current_warning} critical={machine.current_critical} />
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="font-medium text-white">Production statistics</h3>
              <p className="mt-1 text-xs text-slate-500">Simulated counts. Actual OEE needs verified production and machine-time data.</p>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <Stat label="Good count" value={machine.good_count.toLocaleString()} />
                <Stat label="Defective count" value={machine.defect_count.toLocaleString()} />
                <Stat label="Running time" value={formatDuration(machine.running_seconds)} />
                <Stat label="Idle time" value={formatDuration(machine.idle_seconds)} />
                <Stat label="Fault downtime" value={formatDuration(machine.fault_seconds)} />
                <Stat label="Stopped time" value={formatDuration(machine.stopped_seconds)} />
                <Stat label="Stops" value={String(machine.stop_count)} />
                <Stat label="Ideal cycle" value={`${machine.ideal_cycle_time} s`} />
              </dl>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Simulated OEE</span>
                  <span>{formatPercent(machine.oee.oee)}</span>
                </div>
                <OeeBar value={machine.oee.oee} />
                <p className="text-xs text-slate-500">
                  Availability {formatPercent(machine.oee.availability)} · Performance {formatPercent(machine.oee.performance)} · Quality {formatPercent(machine.oee.quality)}
                </p>
              </div>
            </article>
            <article className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="font-medium text-white">Configured thresholds</h3>
              <p className="mt-1 text-xs text-slate-500">These are simulation parameters, not universal industrial safety limits.</p>
              <table className="mt-4 w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-500">
                  <tr>
                    <th className="py-2">Sensor</th>
                    <th>Normal</th>
                    <th>Warning</th>
                    <th>Critical</th>
                  </tr>
                </thead>
                <tbody className="text-slate-200">
                  <tr className="border-t border-slate-800">
                    <td className="py-2">Temperature</td>
                    <td>{machine.temp_min}–{machine.temp_max} °C</td>
                    <td>{machine.temp_warning} °C</td>
                    <td>{machine.temp_critical} °C</td>
                  </tr>
                  <tr className="border-t border-slate-800">
                    <td className="py-2">Vibration</td>
                    <td>{machine.vib_min}–{machine.vib_max} mm/s</td>
                    <td>{machine.vib_warning} mm/s</td>
                    <td>{machine.vib_critical} mm/s</td>
                  </tr>
                  <tr className="border-t border-slate-800">
                    <td className="py-2">Motor current</td>
                    <td>{machine.current_min}–{machine.current_max} A</td>
                    <td>{machine.current_warning} A</td>
                    <td>{machine.current_critical} A</td>
                  </tr>
                </tbody>
              </table>
            </article>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="font-medium text-white">Demo scenarios</h3>
            <p className="mt-1 mb-3 text-sm text-slate-400">Trigger a reproducible event on this machine. A fault does not clear when the alarm is acknowledged.</p>
            <ScenarioPanel machineId={machine.id} machineName={machine.name} onDone={reload} />
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="font-medium text-white">Status history</h3>
              {data.status_history.length === 0 ? (
                <p className="mt-3 text-sm text-slate-400">No status changes recorded.</p>
              ) : (
                <ul className="mt-3 space-y-3">
                  {data.status_history.map((event) => (
                    <li key={`${event.timestamp}-${event.status}`} className="border-l-2 border-slate-700 pl-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge status={event.status} />
                        <span className="text-xs text-slate-500">{formatTime(event.timestamp)}</span>
                      </div>
                      <p className="mt-1 text-sm text-slate-300">{event.note}</p>
                    </li>
                  ))}
                </ul>
              )}
            </article>
            <article className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="font-medium text-white">Recent alarms</h3>
              {data.alarms.length === 0 ? (
                <p className="mt-3 text-sm text-slate-400">No alarms for this machine.</p>
              ) : (
                <ul className="mt-3 space-y-3">
                  {data.alarms.map((alarm) => (
                    <li key={alarm.id} className="rounded-lg border border-slate-800 p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <SeverityBadge severity={alarm.severity} />
                        <span className="text-sm text-slate-200">{alarm.alarm_type}</span>
                        <span className="text-xs text-slate-500">{alarm.active ? 'Active' : 'Cleared'}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate-300">{alarm.description}</p>
                      <p className="mt-1 text-xs text-slate-500">{formatTime(alarm.timestamp)}</p>
                      {!alarm.acknowledged ? (
                        <button type="button" className="mt-2 text-sm text-sky-300 hover:text-sky-200" onClick={() => void acknowledge(alarm.id)}>
                          Acknowledge
                        </button>
                      ) : (
                        <p className="mt-2 text-xs text-emerald-300">Acknowledged {formatTime(alarm.acknowledged_at)}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </section>
        </>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="text-slate-100">{value}</dd>
    </div>
  )
}
