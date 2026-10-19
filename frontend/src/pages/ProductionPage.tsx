import { downloadCsv } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import type { ProductionSummary } from '../types'
import { formatDuration, formatPercent } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { Banner, buttonClass } from '../components/Banner'
import { KpiCard, OeeBar } from '../components/KpiCard'

export function ProductionPage() {
  const { push } = useToast()
  const { data, error, loading } = usePolling<ProductionSummary>('/api/production/summary', 2500)

  async function exportSummary() {
    try {
      await downloadCsv('/api/production/export', 'production-summary.csv')
      push('Production summary exported.', 'success')
    } catch (caught) {
      push(caught instanceof Error ? caught.message : 'Export failed', 'error')
    }
  }

  return (
    <div className="space-y-4">
      {error && <Banner tone="error">{error}</Banner>}
      {loading && !data && <p className="text-sm text-slate-400">Loading production data…</p>}
      {data && (
        <>
          <Banner tone="info">
            <strong className="font-semibold">Simulated metrics. </strong>
            {data.disclaimer}
          </Banner>
          <div className="flex justify-end">
            <button type="button" className={buttonClass('primary')} onClick={() => void exportSummary()}>
              Export production
            </button>
          </div>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Total count" value={data.totals.production_count.toLocaleString()} hint="All simulated machines" />
            <KpiCard label="Good count" value={data.totals.good_count.toLocaleString()} />
            <KpiCard label="Defective count" value={data.totals.defect_count.toLocaleString()} />
            <KpiCard label="Plant OEE" value={formatPercent(data.totals.oee.oee)} hint="Availability × performance × quality" />
          </section>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Running time" value={formatDuration(data.totals.running_seconds)} hint="Operating time" />
            <KpiCard label="Idle time" value={formatDuration(data.totals.idle_seconds)} hint="Available, not producing" />
            <KpiCard label="Fault downtime" value={formatDuration(data.totals.fault_seconds)} />
            <KpiCard label="Stops" value={String(data.totals.stop_count)} hint="Entries into STOPPED or FAULT" />
          </section>
          <article className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 text-sm text-slate-300">
            <h3 className="font-medium text-white">How this simulator calculates OEE</h3>
            <ul className="mt-3 space-y-1">
              {Object.entries(data.formula).map(([key, value]) => (
                <li key={key}>
                  <span className="text-slate-400">{key.replaceAll('_', ' ')}:</span> {value}
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-slate-500">
              Each factor is capped at 100% before multiplication. Idle time is included in planned production time, so idle operation lowers availability. Downtime is fault time plus stopped time.
            </p>
          </article>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Machine</th>
                  <th className="px-4 py-3">Total</th>
                  <th className="px-4 py-3">Good</th>
                  <th className="px-4 py-3">Defective</th>
                  <th className="px-4 py-3">Running</th>
                  <th className="px-4 py-3">Idle</th>
                  <th className="px-4 py-3">Downtime</th>
                  <th className="px-4 py-3">Stops</th>
                  <th className="px-4 py-3">OEE</th>
                </tr>
              </thead>
              <tbody>
                {data.machines.map((machine) => (
                  <tr key={machine.machine_id} className="border-t border-slate-800">
                    <td className="px-4 py-3">
                      <p>{machine.machine_name}</p>
                      <p className="font-mono text-xs text-slate-500">{machine.machine_id}</p>
                    </td>
                    <td className="px-4 py-3">{machine.production_count}</td>
                    <td className="px-4 py-3">{machine.good_count}</td>
                    <td className="px-4 py-3">{machine.defect_count}</td>
                    <td className="px-4 py-3">{formatDuration(machine.running_seconds)}</td>
                    <td className="px-4 py-3">{formatDuration(machine.idle_seconds)}</td>
                    <td className="px-4 py-3">{formatDuration(machine.downtime_seconds)}</td>
                    <td className="px-4 py-3">{machine.stop_count}</td>
                    <td className="px-4 py-3 min-w-40">
                      <div className="mb-1">{formatPercent(machine.oee.oee)}</div>
                      <OeeBar value={machine.oee.oee} />
                      <p className="mt-1 text-xs text-slate-500">
                        A {formatPercent(machine.oee.availability)} · P {formatPercent(machine.oee.performance)} · Q {formatPercent(machine.oee.quality)}
                      </p>
                    </td>
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
