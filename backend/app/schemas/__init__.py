"""Pydantic models for API input and output."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class OeeOut(BaseModel):
    availability: float
    performance: float
    quality: float
    performance_raw: float
    oee: float
    operating_seconds: float
    planned_seconds: float
    downtime_seconds: float


class MachineOut(BaseModel):
    id: str
    name: str
    machine_type: str
    description: str
    status: str
    temperature: float
    vibration: float
    motor_current: float
    production_count: int
    good_count: int
    defect_count: int
    running_seconds: float
    idle_seconds: float
    fault_seconds: float
    stopped_seconds: float
    downtime_seconds: float
    stop_count: int
    ideal_cycle_time: float
    defect_rate: float
    last_update: str | None
    active_scenario: str | None
    active_alarm_count: int
    temp_min: float
    temp_max: float
    temp_warning: float
    temp_critical: float
    vib_min: float
    vib_max: float
    vib_warning: float
    vib_critical: float
    current_min: float
    current_max: float
    current_warning: float
    current_critical: float
    oee: OeeOut


class ReadingOut(BaseModel):
    timestamp: str
    status: str
    temperature: float
    vibration: float
    motor_current: float


class StatusEventOut(BaseModel):
    timestamp: str
    status: str
    note: str


class AlarmOut(BaseModel):
    id: int
    machine_id: str
    machine_name: str
    alarm_type: str
    severity: str
    description: str
    timestamp: str
    updated_at: str
    acknowledged: bool
    acknowledged_at: str | None
    active: bool
    cleared_at: str | None


class HistoryOut(BaseModel):
    machine: MachineOut
    readings: list[ReadingOut]
    status_history: list[StatusEventOut]
    alarms: list[AlarmOut]


class ActionOut(BaseModel):
    message: str
    machine: MachineOut


class HealthOut(BaseModel):
    status: str
    simulation: str
    simulation_speed: float
    database: str


class SimulationOut(BaseModel):
    state: str
    message: str
    simulation_speed: float


class ScenarioIn(BaseModel):
    machine_id: str = Field(min_length=1, max_length=32)


class MachineThresholdsIn(BaseModel):
    machine_id: str = Field(min_length=1, max_length=32)
    temp_warning: float = Field(gt=0, le=250)
    temp_critical: float = Field(gt=0, le=300)
    vib_warning: float = Field(gt=0, le=50)
    vib_critical: float = Field(gt=0, le=80)
    current_warning: float = Field(gt=0, le=200)
    current_critical: float = Field(gt=0, le=400)

    @model_validator(mode="after")
    def thresholds_increase(self) -> "MachineThresholdsIn":
        if self.temp_warning >= self.temp_critical:
            raise ValueError("Temperature warning threshold must be below the critical threshold.")
        if self.vib_warning >= self.vib_critical:
            raise ValueError("Vibration warning threshold must be below the critical threshold.")
        if self.current_warning >= self.current_critical:
            raise ValueError("Motor current warning threshold must be below the critical threshold.")
        return self


class SettingsIn(BaseModel):
    simulation_speed: float = Field(ge=0.25, le=5)
    machines: list[MachineThresholdsIn] = Field(min_length=1)


class MachineSettingsOut(BaseModel):
    machine_id: str
    name: str
    temp_min: float
    temp_max: float
    temp_warning: float
    temp_critical: float
    vib_min: float
    vib_max: float
    vib_warning: float
    vib_critical: float
    current_min: float
    current_max: float
    current_warning: float
    current_critical: float


class SettingsOut(BaseModel):
    simulation_speed: float
    tick_interval_seconds: float
    simulation: str
    machines: list[MachineSettingsOut]


class ProductionMachineOut(BaseModel):
    machine_id: str
    machine_name: str
    status: str
    production_count: int
    good_count: int
    defect_count: int
    running_seconds: float
    idle_seconds: float
    fault_seconds: float
    stopped_seconds: float
    downtime_seconds: float
    stop_count: int
    ideal_cycle_time: float
    oee: OeeOut


class ProductionSummaryOut(BaseModel):
    simulated: bool
    disclaimer: str
    formula: dict[str, str]
    totals: ProductionMachineOut
    machines: list[ProductionMachineOut]


class ReportBarOut(BaseModel):
    machine_id: str
    machine_name: str
    running_seconds: float
    idle_seconds: float
    downtime_seconds: float
    fault_seconds: float
    stopped_seconds: float
    alarm_count: int
    warning_count: int
    critical_count: int
    info_count: int
    production_count: int
    good_count: int
    defect_count: int
    oee: float
    availability: float
    performance: float
    quality: float


class TrendPointOut(BaseModel):
    timestamp: str
    temperature: float
    vibration: float
    motor_current: float


class MachineTrendOut(BaseModel):
    machine_id: str
    machine_name: str
    points: list[TrendPointOut]


class ReportSummaryOut(BaseModel):
    simulated: bool
    disclaimer: str
    from_timestamp: str | None
    to_timestamp: str | None
    machines: list[ReportBarOut]
    trends: list[MachineTrendOut]
