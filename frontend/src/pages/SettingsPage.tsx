import { useEffect, useState } from 'react'
import { getSettings, saveSettings } from '../services/api'
import type { MachineSettings, Settings } from '../types'
import { useToast } from '../context/ToastContext'
import { usePolling } from '../hooks/usePolling'
import type { Health } from '../types'
import { Banner, buttonClass } from '../components/Banner'
import { ScenarioPanel } from '../components/ScenarioPanel'
import { SimulationControls } from '../components/SimulationControls'

type Draft = MachineSettings

export function SettingsPage() {
  const { push } = useToast()
  const health = usePolling<Health>('/api/health', 2500)
  const [speed, setSpeed] = useState(1)
  const [tick, setTick] = useState(2.5)
  const [rows, setRows] = useState<Draft[]>([])
  const [machineId, setMachineId] = useState('MCH-A')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let cancelled = false
    getSettings()
      .then((settings) => {
        if (cancelled) return
        applySettings(settings)
        setError(null)
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : 'Could not load settings')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  function applySettings(settings: Settings) {
    setSpeed(settings.simulation_speed)
    setTick(settings.tick_interval_seconds)
    setRows(settings.machines)
    if (settings.machines[0] && !settings.machines.some((machine) => machine.machine_id === machineId)) {
      setMachineId(settings.machines[0].machine_id)
    }
  }

  function update(id: string, field: keyof Draft, value: number) {
    setRows((current) => current.map((row) => (row.machine_id === id ? { ...row, [field]: value } : row)))
  }

  async function save() {
    setSaving(true)
    try {
      const saved = await saveSettings({
        simulation_speed: speed,
        machines: rows.map((row) => ({
          machine_id: row.machine_id,
          temp_warning: row.temp_warning,
          temp_critical: row.temp_critical,
          vib_warning: row.vib_warning,
          vib_critical: row.vib_critical,
          current_warning: row.current_warning,
          current_critical: row.current_critical,
        })),
      })
      applySettings(saved)
      push('Settings saved.', 'success')
      setError(null)
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Settings were rejected'
      setError(message)
      push(message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const selected = rows.find((row) => row.machine_id === machineId)

  return (
    <div className="space-y-5">
      <Banner tone="info">
        Thresholds are simulation parameters for this academic project. They are not universal industrial safety limits. Warning values must stay at or above each sensor&apos;s normal maximum, and below the critical value.
      </Banner>
      {error && <Banner tone="error">{error}</Banner>}
      {loading && <p className="text-sm text-slate-400">Loading settings…</p>}
      {!loading && (
        <>
          <section className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="font-medium text-white">Simulation control</h3>
            <p className="mt-1 text-sm text-slate-400">
              One background loop updates all machines. At the saved speed, a tick is about every {tick.toFixed(2)} seconds.
            </p>
            <div className="mt-4">
              <SimulationControls state={health.data?.simulation} onDone={health.reload} />
            </div>
            <label className="mt-4 block max-w-xs text-sm text-slate-300">
              Simulation speed (0.25 to 5)
              <input
                type="number"
                min={0.25}
                max={5}
                step={0.25}
                value={speed}
                onChange={(event) => setSpeed(Number(event.target.value))}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              />
            </label>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="font-medium text-white">Trigger a simulated event</h3>
            <label className="mt-3 block max-w-sm text-sm text-slate-300">
              Machine
              <select className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={machineId} onChange={(event) => setMachineId(event.target.value)}>
                {rows.map((row) => (
                  <option key={row.machine_id} value={row.machine_id}>
                    {row.name}
                  </option>
                ))}
              </select>
            </label>
            {selected && (
              <div className="mt-4">
                <ScenarioPanel machineId={selected.machine_id} machineName={selected.name} onDone={() => undefined} />
              </div>
            )}
          </section>

          <section className="space-y-4">
            {rows.map((row) => (
              <article key={row.machine_id} className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
                <h3 className="font-medium text-white">
                  {row.name} <span className="font-mono text-xs text-slate-500">{row.machine_id}</span>
                </h3>
                <div className="mt-4 grid gap-4 lg:grid-cols-3">
                  <ThresholdGroup
                    title="Temperature (°C)"
                    normal={`${row.temp_min}–${row.temp_max}`}
                    warning={row.temp_warning}
                    critical={row.temp_critical}
                    onWarning={(value) => update(row.machine_id, 'temp_warning', value)}
                    onCritical={(value) => update(row.machine_id, 'temp_critical', value)}
                  />
                  <ThresholdGroup
                    title="Vibration (mm/s)"
                    normal={`${row.vib_min}–${row.vib_max}`}
                    warning={row.vib_warning}
                    critical={row.vib_critical}
                    onWarning={(value) => update(row.machine_id, 'vib_warning', value)}
                    onCritical={(value) => update(row.machine_id, 'vib_critical', value)}
                  />
                  <ThresholdGroup
                    title="Motor current (A)"
                    normal={`${row.current_min}–${row.current_max}`}
                    warning={row.current_warning}
                    critical={row.current_critical}
                    onWarning={(value) => update(row.machine_id, 'current_warning', value)}
                    onCritical={(value) => update(row.machine_id, 'current_critical', value)}
                  />
                </div>
              </article>
            ))}
          </section>
          <button type="button" className={buttonClass('primary')} disabled={saving} onClick={() => void save()}>
            {saving ? 'Saving…' : 'Save settings'}
          </button>
        </>
      )}
    </div>
  )
}

function ThresholdGroup({
  title,
  normal,
  warning,
  critical,
  onWarning,
  onCritical,
}: {
  title: string
  normal: string
  warning: number
  critical: number
  onWarning: (value: number) => void
  onCritical: (value: number) => void
}) {
  return (
    <div>
      <p className="text-sm text-slate-200">{title}</p>
      <p className="text-xs text-slate-500">Normal range {normal}</p>
      <label className="mt-2 block text-xs text-slate-400">
        Warning
        <input type="number" step="0.1" value={warning} onChange={(event) => onWarning(Number(event.target.value))} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
      </label>
      <label className="mt-2 block text-xs text-slate-400">
        Critical
        <input type="number" step="0.1" value={critical} onChange={(event) => onCritical(Number(event.target.value))} className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
      </label>
    </div>
  )
}
