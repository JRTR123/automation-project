import { useMemo, useState } from 'react'
import { acknowledgeAlarm, downloadCsv } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import type { Alarm, Machine } from '../types'
import { formatTime } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { Banner, buttonClass } from '../components/Banner'
import { SeverityBadge } from '../components/StatusBadge'

export function AlarmsPage() {
  const { push } = useToast()
  const machines = usePolling<Machine[]>('/api/machines', 10000)
  const [machineId, setMachineId] = useState('')
  const [severity, setSeverity] = useState('')
  const [acknowledged, setAcknowledged] = useState('')

  const query = useMemo(() => {
    const params = new URLSearchParams()
    if (machineId) params.set('machine_id', machineId)
    if (severity) params.set('severity', severity)
    if (acknowledged === 'yes') params.set('acknowledged', 'true')
    if (acknowledged === 'no') params.set('acknowledged', 'false')
    const text = params.toString()
    return text ? `?${text}` : ''
  }, [machineId, severity, acknowledged])

  const alarms = usePolling<Alarm[]>(`/api/alarms${query}`, 2500)

  async function acknowledge(alarm: Alarm) {
    try {
      await acknowledgeAlarm(alarm.id)
      push(`Acknowledged alarm ${alarm.id}. ${alarm.machine_name} was not reset.`, 'success')
      alarms.reload()
    } catch (error) {
      push(error instanceof Error ? error.message : 'Could not acknowledge the alarm', 'error')
    }
  }

  async function exportAlarms() {
    try {
      await downloadCsv(`/api/alarms/export${query}`, 'alarm-history.csv')
      push('Alarm history exported.', 'success')
    } catch (error) {
      push(error instanceof Error ? error.message : 'Export failed', 'error')
    }
  }

  return (
    <div className="space-y-4">
      <Banner tone="info">
        Acknowledgment records that an operator has seen the alarm. It does not clear a machine fault. Use Reset on the machine to recover from FAULT.
      </Banner>
      {(alarms.error || machines.error) && <Banner tone="error">{alarms.error || machines.error}</Banner>}
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm text-slate-300">
          Machine
          <select className="mt-1 block rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={machineId} onChange={(event) => setMachineId(event.target.value)}>
            <option value="">All machines</option>
            {(machines.data ?? []).map((machine) => (
              <option key={machine.id} value={machine.id}>
                {machine.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-300">
          Severity
          <select className="mt-1 block rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="">All severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </label>
        <label className="text-sm text-slate-300">
          Acknowledgment
          <select className="mt-1 block rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={acknowledged} onChange={(event) => setAcknowledged(event.target.value)}>
            <option value="">All</option>
            <option value="no">Unacknowledged</option>
            <option value="yes">Acknowledged</option>
          </select>
        </label>
        <button type="button" className={buttonClass('primary')} onClick={() => void exportAlarms()}>
          Export alarms
        </button>
      </div>
      {alarms.loading && !alarms.data && <p className="text-sm text-slate-400">Loading alarms…</p>}
      {alarms.data && alarms.data.length === 0 && <Banner tone="info">No alarms match the current filters.</Banner>}
      {alarms.data && alarms.data.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Machine</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {alarms.data.map((alarm) => (
                <tr key={alarm.id} className="border-t border-slate-800 align-top">
                  <td className="px-4 py-3 font-mono text-xs">{alarm.id}</td>
                  <td className="px-4 py-3">{alarm.machine_name}</td>
                  <td className="px-4 py-3">{alarm.alarm_type}</td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={alarm.severity} />
                  </td>
                  <td className="max-w-md px-4 py-3 text-slate-300">{alarm.description}</td>
                  <td className="px-4 py-3 text-slate-400">{formatTime(alarm.timestamp)}</td>
                  <td className="px-4 py-3">
                    <p>{alarm.active ? 'Active' : 'Cleared'}</p>
                    <p className="text-xs text-slate-500">{alarm.acknowledged ? `Ack ${formatTime(alarm.acknowledged_at)}` : 'Unacknowledged'}</p>
                  </td>
                  <td className="px-4 py-3">
                    {alarm.acknowledged ? (
                      <span className="text-xs text-emerald-300">Recorded</span>
                    ) : (
                      <button type="button" className={buttonClass('primary')} onClick={() => void acknowledge(alarm)}>
                        Acknowledge
                      </button>
                    )}
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
