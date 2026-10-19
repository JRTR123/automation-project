import { useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { downloadCsv } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import type { ReportSummary } from '../types'
import { formatPercent } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { Banner, buttonClass } from '../components/Banner'
import { SensorChart } from '../components/SensorChart'

export function ReportsPage() {
  const { push } = useToast()
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [applied, setApplied] = useState({ from: '', to: '' })
  const [machineId, setMachineId] = useState('MCH-A')

  const query = useMemo(() => {
    const params = new URLSearchParams()
    if (applied.from) params.set('from', new Date(applied.from).toISOString())
    if (applied.to) params.set('to', new Date(applied.to).toISOString())
    const text = params.toString()
    return text ? `?${text}` : ''
  }, [applied])

  const report = usePolling<ReportSummary>(`/api/reports/summary${query}`, 5000)
  const selected = report.data?.trends.find((trend) => trend.machine_id === machineId) ?? report.data?.trends[0]

  async function exportFile(path: string, filename: string) {
    try {
      await downloadCsv(path, filename)
      push(`${filename} downloaded.`, 'success')
    } catch (error) {
      push(error instanceof Error ? error.message : 'Export failed', 'error')
    }
  }

  const rows = report.data?.machines ?? []
  const chartRows = rows.map((row) => ({
    name: row.machine_name.replace(' System', '').replace(' Machine', '').replace(' Station', '').replace('Electric ', ''),
    running: row.running_seconds,
    downtime: row.downtime_seconds,
    alarms: row.alarm_count,
    production: row.production_count,
    oee: Number((row.oee * 100).toFixed(1)),
  }))

  return (
    <div className="space-y-4">
      {report.error && <Banner tone="error">{report.error}</Banner>}
      {report.data && <Banner tone="info">{report.data.disclaimer} Charts on this page use the report response from the API.</Banner>}
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm text-slate-300">
          From
          <input type="datetime-local" className="mt-1 block rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={from} onChange={(event) => setFrom(event.target.value)} />
        </label>
        <label className="text-sm text-slate-300">
          To
          <input type="datetime-local" className="mt-1 block rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={to} onChange={(event) => setTo(event.target.value)} />
        </label>
        <button type="button" className={buttonClass('primary')} onClick={() => setApplied({ from, to })}>
          Apply dates
        </button>
        <button
          type="button"
          className={buttonClass()}
          onClick={() => {
            setFrom('')
            setTo('')
            setApplied({ from: '', to: '' })
          }}
        >
          Clear dates
        </button>
        <button type="button" className={buttonClass()} onClick={() => void exportFile('/api/alarms/export', 'alarm-history.csv')}>
          Export alarms
        </button>
        <button type="button" className={buttonClass()} onClick={() => void exportFile('/api/production/export', 'production-summary.csv')}>
          Export production
        </button>
      </div>
      {report.loading && !report.data && <p className="text-sm text-slate-400">Loading report data…</p>}
      {report.data && rows.length === 0 && <Banner tone="info">No report rows were returned.</Banner>}
      {report.data && rows.length > 0 && (
        <>
          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard title="Uptime and downtime (simulated seconds)">
              <BarChart data={chartRows}>
                <CartesianGrid stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Legend />
                <Bar dataKey="running" fill="#34d399" name="Running" />
                <Bar dataKey="downtime" fill="#f87171" name="Downtime" />
              </BarChart>
            </ChartCard>
            <ChartCard title="Alarm frequency">
              <BarChart data={chartRows}>
                <CartesianGrid stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Bar dataKey="alarms" fill="#fbbf24" name="Alarms" />
              </BarChart>
            </ChartCard>
            <ChartCard title="Production counts">
              <BarChart data={chartRows}>
                <CartesianGrid stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Bar dataKey="production" fill="#38bdf8" name="Total count" />
              </BarChart>
            </ChartCard>
            <ChartCard title="OEE summary (%)">
              <BarChart data={chartRows}>
                <CartesianGrid stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Bar dataKey="oee" fill="#a78bfa" name="OEE %" />
              </BarChart>
            </ChartCard>
          </section>
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-sm text-slate-300">
              Sensor trend
              <select className="mt-1 block rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={selected?.machine_id ?? ''} onChange={(event) => setMachineId(event.target.value)}>
                {report.data.trends.map((trend) => (
                  <option key={trend.machine_id} value={trend.machine_id}>
                    {trend.machine_name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {selected && (
            <section className="grid gap-4 xl:grid-cols-3">
              <SensorChart title={`${selected.machine_name} temperature`} data={selected.points} dataKey="temperature" color="#fbbf24" unit="°C" warning={0} critical={0} />
              <SensorChart title={`${selected.machine_name} vibration`} data={selected.points} dataKey="vibration" color="#38bdf8" unit="mm/s" warning={0} critical={0} />
              <SensorChart title={`${selected.machine_name} current`} data={selected.points} dataKey="motor_current" color="#a78bfa" unit="A" warning={0} critical={0} />
            </section>
          )}
          {selected && selected.points.length === 0 && <Banner tone="info">No sensor samples fall inside the selected dates.</Banner>}
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Machine</th>
                  <th className="px-4 py-3">Running</th>
                  <th className="px-4 py-3">Downtime</th>
                  <th className="px-4 py-3">Alarms</th>
                  <th className="px-4 py-3">Production</th>
                  <th className="px-4 py-3">OEE</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.machine_id} className="border-t border-slate-800">
                    <td className="px-4 py-3">{row.machine_name}</td>
                    <td className="px-4 py-3">{row.running_seconds.toFixed(0)} s</td>
                    <td className="px-4 py-3">{row.downtime_seconds.toFixed(0)} s</td>
                    <td className="px-4 py-3">{row.alarm_count}</td>
                    <td className="px-4 py-3">{row.production_count}</td>
                    <td className="px-4 py-3">{formatPercent(row.oee)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactElement }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
      <h3 className="mb-3 text-sm font-medium text-white">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer>
      </div>
    </section>
  )
}
