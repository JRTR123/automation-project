"""Machine commands, settings updates, and API serialization."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import now_ts, to_iso
from app.models.entities import AppSetting, Machine, StatusEvent
from app.schemas import MachineOut, OeeOut
from app.services.alarms import active_alarm_count, deactivate_machine_alarms, record_info
from app.services.catalog import BASE_TICK_SECONDS, MIN_TICK_SECONDS
from app.services.oee import calculate_oee


def list_machines(db: Session) -> list[Machine]:
    return list(db.scalars(select(Machine).order_by(Machine.id)).all())


def get_machine(db: Session, machine_id: str) -> Machine:
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise AppError(f"Machine {machine_id} was not found.", 404)
    return machine


def set_status(db: Session, machine: Machine, status: str, note: str, timestamp: float | None = None) -> None:
    if machine.status == status:
        return
    if status in {"STOPPED", "FAULT"}:
        machine.stop_count += 1
    moment = timestamp if timestamp is not None else now_ts()
    machine.status = status
    db.add(StatusEvent(machine_id=machine.id, timestamp=moment, status=status, note=note))


def start_machine(db: Session, machine_id: str) -> tuple[str, Machine]:
    machine = get_machine(db, machine_id)
    if machine.status == "FAULT":
        raise AppError("Machine is in fault. Reset it before starting.", 409)
    if machine.status == "RUNNING" and machine.active_scenario != "idle":
        return f"{machine.name} is already running.", machine
    if machine.active_scenario == "idle":
        machine.active_scenario = None
    set_status(db, machine, "RUNNING", "Operator started the machine.")
    return f"{machine.name} is running.", machine


def stop_machine(db: Session, machine_id: str) -> tuple[str, Machine]:
    machine = get_machine(db, machine_id)
    if machine.status == "FAULT":
        raise AppError("Machine is in fault. Reset it to recover instead of using stop.", 409)
    if machine.status == "STOPPED":
        return f"{machine.name} is already stopped.", machine
    if machine.active_scenario == "idle":
        machine.active_scenario = None
    set_status(db, machine, "STOPPED", "Operator stopped the machine.")
    return f"{machine.name} is stopped.", machine


def reset_machine(db: Session, machine_id: str) -> tuple[str, Machine]:
    machine = get_machine(db, machine_id)
    moment = now_ts()
    machine.active_scenario = None
    machine.cycle_accumulator = 0.0
    machine.temperature = round((machine.temp_min + machine.temp_max) / 2, 2)
    machine.vibration = round((machine.vib_min + machine.vib_max) / 2, 3)
    machine.motor_current = round((machine.current_min + machine.current_max) / 2, 2)
    deactivate_machine_alarms(db, machine, moment)
    set_status(db, machine, "IDLE", "Operator reset the machine. Fault and scenario cleared. Alarms were not acknowledged.")
    record_info(
        db,
        machine,
        "MACHINE_RESET",
        (
            f"Operator reset: {machine.name} returned to IDLE. "
            "The fault condition and active scenario were cleared. Acknowledgment history was not changed."
        ),
        moment,
    )
    return (
        f"{machine.name} was reset to IDLE. Active alarms were cleared but not acknowledged.",
        machine,
    )


def midpoint_sensors(machine: Machine) -> None:
    machine.temperature = (machine.temp_min + machine.temp_max) / 2
    machine.vibration = (machine.vib_min + machine.vib_max) / 2
    machine.motor_current = (machine.current_min + machine.current_max) / 2


def serialize_machine(db: Session, machine: Machine) -> MachineOut:
    oee = calculate_oee(
        machine.running_seconds,
        machine.idle_seconds,
        machine.fault_seconds,
        machine.stopped_seconds,
        machine.production_count,
        machine.good_count,
        machine.ideal_cycle_time,
    )
    payload = {
        "id": machine.id,
        "name": machine.name,
        "machine_type": machine.machine_type,
        "description": machine.description,
        "status": machine.status,
        "temperature": round(machine.temperature, 2),
        "vibration": round(machine.vibration, 3),
        "motor_current": round(machine.motor_current, 2),
        "production_count": machine.production_count,
        "good_count": machine.good_count,
        "defect_count": machine.defect_count,
        "running_seconds": round(machine.running_seconds, 1),
        "idle_seconds": round(machine.idle_seconds, 1),
        "fault_seconds": round(machine.fault_seconds, 1),
        "stopped_seconds": round(machine.stopped_seconds, 1),
        "downtime_seconds": round(machine.fault_seconds + machine.stopped_seconds, 1),
        "stop_count": machine.stop_count,
        "ideal_cycle_time": machine.ideal_cycle_time,
        "defect_rate": machine.defect_rate,
        "last_update": to_iso(machine.last_update) if machine.last_update else None,
        "active_scenario": machine.active_scenario,
        "active_alarm_count": active_alarm_count(db, machine.id),
        "temp_min": machine.temp_min,
        "temp_max": machine.temp_max,
        "temp_warning": machine.temp_warning,
        "temp_critical": machine.temp_critical,
        "vib_min": machine.vib_min,
        "vib_max": machine.vib_max,
        "vib_warning": machine.vib_warning,
        "vib_critical": machine.vib_critical,
        "current_min": machine.current_min,
        "current_max": machine.current_max,
        "current_warning": machine.current_warning,
        "current_critical": machine.current_critical,
        "oee": OeeOut(**oee),
    }
    return MachineOut(**payload)


def tick_interval(speed: float) -> float:
    return max(MIN_TICK_SECONDS, BASE_TICK_SECONDS / max(speed, 0.25))


def get_settings_row(db: Session) -> AppSetting:
    row = db.get(AppSetting, 1)
    if row is None:
        row = AppSetting(id=1, simulation_speed=1.0, paused=False)
        db.add(row)
        db.flush()
    return row


def update_thresholds(db: Session, speed: float, machines_in: list) -> None:
    row = get_settings_row(db)
    row.simulation_speed = speed
    seen: set[str] = set()
    for item in machines_in:
        if item.machine_id in seen:
            raise AppError("Each machine can appear only once in settings.", 422)
        seen.add(item.machine_id)
        machine = get_machine(db, item.machine_id)
        _check_band(machine.name, "Temperature", item.temp_warning, item.temp_critical, machine.temp_max)
        _check_band(machine.name, "Vibration", item.vib_warning, item.vib_critical, machine.vib_max)
        _check_band(machine.name, "Motor current", item.current_warning, item.current_critical, machine.current_max)
        machine.temp_warning = item.temp_warning
        machine.temp_critical = item.temp_critical
        machine.vib_warning = item.vib_warning
        machine.vib_critical = item.vib_critical
        machine.current_warning = item.current_warning
        machine.current_critical = item.current_critical


def _check_band(machine_name: str, label: str, warning: float, critical: float, normal_max: float) -> None:
    if warning < normal_max:
        raise AppError(
            f"{machine_name}: {label.lower()} warning ({warning:g}) must be at or above the normal maximum ({normal_max:g}).",
            422,
        )
    if warning >= critical:
        raise AppError(f"{machine_name}: {label.lower()} warning must be below the critical threshold.", 422)
