import { pauseSimulation, resumeSimulation, startSimulation } from '../services/api'
import type { SimulationStateName } from '../types'
import { useToast } from '../context/ToastContext'
import { buttonClass } from './Banner'

export function SimulationControls({
  state,
  onDone,
}: {
  state: SimulationStateName | undefined
  onDone?: () => void
}) {
  const { push } = useToast()

  async function run(action: () => Promise<{ message: string }>) {
    try {
      const result = await action()
      push(result.message, 'success')
      onDone?.()
    } catch (error) {
      push(error instanceof Error ? error.message : 'Simulation command failed', 'error')
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        className={buttonClass('primary')}
        disabled={state === 'running' || state === 'paused'}
        onClick={() => void run(startSimulation)}
      >
        Start simulation
      </button>
      <button type="button" className={buttonClass()} disabled={state !== 'running'} onClick={() => void run(pauseSimulation)}>
        Pause simulation
      </button>
      <button type="button" className={buttonClass('primary')} disabled={state !== 'paused'} onClick={() => void run(resumeSimulation)}>
        Resume simulation
      </button>
    </div>
  )
}
