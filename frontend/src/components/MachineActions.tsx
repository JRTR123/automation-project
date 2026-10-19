import { useState } from 'react'
import { resetMachine, startMachine, stopMachine } from '../services/api'
import type { MachineStatus } from '../types'
import { useToast } from '../context/ToastContext'
import { buttonClass } from './Banner'
import { ConfirmDialog } from './ConfirmDialog'

export function MachineActions({
  machineId,
  machineName,
  status,
  onDone,
}: {
  machineId: string
  machineName: string
  status: MachineStatus
  onDone: () => void
}) {
  const { push } = useToast()
  const [pending, setPending] = useState(false)
  const [confirmReset, setConfirmReset] = useState(false)

  async function run(action: () => Promise<{ message: string }>) {
    setPending(true)
    try {
      const result = await action()
      push(result.message, 'success')
      onDone()
    } catch (error) {
      push(error instanceof Error ? error.message : 'Action failed', 'error')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        className={buttonClass('primary')}
        disabled={pending || status === 'FAULT' || status === 'RUNNING'}
        aria-label={`Start ${machineName}`}
        onClick={() => void run(() => startMachine(machineId))}
      >
        Start
      </button>
      <button
        type="button"
        className={buttonClass()}
        disabled={pending || status === 'FAULT' || status === 'STOPPED'}
        aria-label={`Stop ${machineName}`}
        onClick={() => void run(() => stopMachine(machineId))}
      >
        Stop
      </button>
      <button
        type="button"
        className={buttonClass('danger')}
        disabled={pending}
        aria-label={`Reset ${machineName}`}
        onClick={() => setConfirmReset(true)}
      >
        Reset
      </button>
      <ConfirmDialog
        open={confirmReset}
        title={`Reset ${machineName}?`}
        message="This clears the fault and the active scenario, then sets the machine to IDLE. Production history is kept. Active alarms are marked cleared, but they are not acknowledged."
        confirmLabel="Reset machine"
        onCancel={() => setConfirmReset(false)}
        onConfirm={() => {
          setConfirmReset(false)
          void run(() => resetMachine(machineId))
        }}
      />
    </div>
  )
}
