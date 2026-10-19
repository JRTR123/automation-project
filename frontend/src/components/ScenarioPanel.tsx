import { useState } from 'react'
import { triggerScenario } from '../services/api'
import { useToast } from '../context/ToastContext'
import { buttonClass } from './Banner'

const SCENARIOS = [
  { id: 'high_temperature', label: 'High temperature', tone: 'ghost' as const },
  { id: 'excessive_vibration', label: 'Excessive vibration', tone: 'ghost' as const },
  { id: 'motor_overload', label: 'Motor overload', tone: 'ghost' as const },
  { id: 'idle', label: 'Idle operation', tone: 'ghost' as const },
  { id: 'machine_fault', label: 'Machine fault', tone: 'danger' as const },
  { id: 'clear', label: 'Clear scenario', tone: 'primary' as const },
]

export function ScenarioPanel({ machineId, machineName, onDone }: { machineId: string; machineName: string; onDone: () => void }) {
  const { push } = useToast()
  const [pending, setPending] = useState<string | null>(null)

  async function run(scenario: string) {
    setPending(scenario)
    try {
      const result = await triggerScenario(scenario, machineId)
      push(result.message, scenario === 'machine_fault' ? 'warning' : 'success')
      onDone()
    } catch (error) {
      push(error instanceof Error ? error.message : 'Scenario failed', 'error')
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {SCENARIOS.map((scenario) => (
        <button
          key={scenario.id}
          type="button"
          className={buttonClass(scenario.tone)}
          disabled={pending !== null}
          aria-label={`${scenario.label} on ${machineName}`}
          onClick={() => void run(scenario.id)}
        >
          {pending === scenario.id ? 'Working…' : scenario.label}
        </button>
      ))}
    </div>
  )
}
