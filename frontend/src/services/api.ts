import type {
  ActionResult,
  Alarm,
  Health,
  History,
  Machine,
  ProductionSummary,
  ReportSummary,
  Settings,
  SettingsUpdate,
  SimulationStatus,
} from '../types'

const OFFLINE = 'Cannot reach the backend. Start the API on http://127.0.0.1:8000.'

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => {
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg: string }).msg)
          }
          return 'Invalid value'
        })
        .join(' ')
    }
  } catch {
    return response.statusText || 'Request failed'
  }
  return response.statusText || 'Request failed'
}

export async function apiGet<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(path)
  } catch {
    throw new Error(OFFLINE)
  }
  if (!response.ok) throw new Error(await errorMessage(response))
  return (await response.json()) as T
}

export async function apiSend<T>(path: string, method: string, body?: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new Error(OFFLINE)
  }
  if (!response.ok) throw new Error(await errorMessage(response))
  return (await response.json()) as T
}

export function getHealth() {
  return apiGet<Health>('/api/health')
}

export function getMachines() {
  return apiGet<Machine[]>('/api/machines')
}

export function getHistory(machineId: string) {
  return apiGet<History>(`/api/machines/${machineId}/history?limit=80`)
}

export function startMachine(machineId: string) {
  return apiSend<ActionResult>(`/api/machines/${machineId}/start`, 'POST')
}

export function stopMachine(machineId: string) {
  return apiSend<ActionResult>(`/api/machines/${machineId}/stop`, 'POST')
}

export function resetMachine(machineId: string) {
  return apiSend<ActionResult>(`/api/machines/${machineId}/reset`, 'POST')
}

export function getAlarms(query = '') {
  return apiGet<Alarm[]>(`/api/alarms${query}`)
}

export function acknowledgeAlarm(alarmId: number) {
  return apiSend<Alarm>(`/api/alarms/${alarmId}/acknowledge`, 'POST')
}

export function getProduction() {
  return apiGet<ProductionSummary>('/api/production/summary')
}

export function getReport(query = '') {
  return apiGet<ReportSummary>(`/api/reports/summary${query}`)
}

export function getSettings() {
  return apiGet<Settings>('/api/settings')
}

export function saveSettings(body: SettingsUpdate) {
  return apiSend<Settings>('/api/settings', 'PUT', body)
}

export function startSimulation() {
  return apiSend<SimulationStatus>('/api/simulation/start', 'POST')
}

export function pauseSimulation() {
  return apiSend<SimulationStatus>('/api/simulation/pause', 'POST')
}

export function resumeSimulation() {
  return apiSend<SimulationStatus>('/api/simulation/resume', 'POST')
}

export function triggerScenario(scenario: string, machineId: string) {
  return apiSend<ActionResult>(`/api/simulation/scenarios/${scenario}`, 'POST', { machine_id: machineId })
}

export async function downloadCsv(path: string, filename: string) {
  let response: Response
  try {
    response = await fetch(path)
  } catch {
    throw new Error(OFFLINE)
  }
  if (!response.ok) throw new Error(await errorMessage(response))
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
