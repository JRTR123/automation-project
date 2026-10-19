export type MachineStatus = 'RUNNING' | 'IDLE' | 'STOPPED' | 'FAULT'
export type Severity = 'INFO' | 'WARNING' | 'CRITICAL'
export type SimulationStateName = 'running' | 'paused' | 'stopped'

export interface OeeMetrics {
  availability: number
  performance: number
  quality: number
  performance_raw: number
  oee: number
  operating_seconds: number
  planned_seconds: number
  downtime_seconds: number
}

export interface Machine {
  id: string
  name: string
  machine_type: string
  description: string
  status: MachineStatus
  temperature: number
  vibration: number
  motor_current: number
  production_count: number
  good_count: number
  defect_count: number
  running_seconds: number
  idle_seconds: number
  fault_seconds: number
  stopped_seconds: number
  downtime_seconds: number
  stop_count: number
  ideal_cycle_time: number
  defect_rate: number
  last_update: string | null
  active_scenario: string | null
  active_alarm_count: number
  temp_min: number
  temp_max: number
  temp_warning: number
  temp_critical: number
  vib_min: number
  vib_max: number
  vib_warning: number
  vib_critical: number
  current_min: number
  current_max: number
  current_warning: number
  current_critical: number
  oee: OeeMetrics
}

export interface Alarm {
  id: number
  machine_id: string
  machine_name: string
  alarm_type: string
  severity: Severity
  description: string
  timestamp: string
  updated_at: string
  acknowledged: boolean
  acknowledged_at: string | null
  active: boolean
  cleared_at: string | null
}

export interface Reading {
  timestamp: string
  status: MachineStatus
  temperature: number
  vibration: number
  motor_current: number
}

export interface StatusEvent {
  timestamp: string
  status: MachineStatus
  note: string
}

export interface History {
  machine: Machine
  readings: Reading[]
  status_history: StatusEvent[]
  alarms: Alarm[]
}

export interface ActionResult {
  message: string
  machine: Machine
}

export interface Health {
  status: string
  simulation: SimulationStateName
  simulation_speed: number
  database: string
}

export interface SimulationStatus {
  state: SimulationStateName
  message: string
  simulation_speed: number
}

export interface MachineSettings {
  machine_id: string
  name: string
  temp_min: number
  temp_max: number
  temp_warning: number
  temp_critical: number
  vib_min: number
  vib_max: number
  vib_warning: number
  vib_critical: number
  current_min: number
  current_max: number
  current_warning: number
  current_critical: number
}

export interface Settings {
  simulation_speed: number
  tick_interval_seconds: number
  simulation: SimulationStateName
  machines: MachineSettings[]
}

export interface SettingsUpdate {
  simulation_speed: number
  machines: Array<Pick<
    MachineSettings,
    | 'machine_id'
    | 'temp_warning'
    | 'temp_critical'
    | 'vib_warning'
    | 'vib_critical'
    | 'current_warning'
    | 'current_critical'
  >>
}

export interface ProductionMachine {
  machine_id: string
  machine_name: string
  status: string
  production_count: number
  good_count: number
  defect_count: number
  running_seconds: number
  idle_seconds: number
  fault_seconds: number
  stopped_seconds: number
  downtime_seconds: number
  stop_count: number
  ideal_cycle_time: number
  oee: OeeMetrics
}

export interface ProductionSummary {
  simulated: boolean
  disclaimer: string
  formula: Record<string, string>
  totals: ProductionMachine
  machines: ProductionMachine[]
}

export interface ReportMachine {
  machine_id: string
  machine_name: string
  running_seconds: number
  idle_seconds: number
  downtime_seconds: number
  fault_seconds: number
  stopped_seconds: number
  alarm_count: number
  warning_count: number
  critical_count: number
  info_count: number
  production_count: number
  good_count: number
  defect_count: number
  oee: number
  availability: number
  performance: number
  quality: number
}

export interface TrendPoint {
  timestamp: string
  temperature: number
  vibration: number
  motor_current: number
}

export interface MachineTrend {
  machine_id: string
  machine_name: string
  points: TrendPoint[]
}

export interface ReportSummary {
  simulated: boolean
  disclaimer: string
  from_timestamp: string | null
  to_timestamp: string | null
  machines: ReportMachine[]
  trends: MachineTrend[]
}
