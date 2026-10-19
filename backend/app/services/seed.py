"""Initial demo data for the four simulated machines."""

from __future__ import annotations

import random

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.timeutil import now_ts
from app.models.entities import Alarm, AppSetting, Machine, MetricSample, StatusEvent
from app.services.catalog import MACHINE_SPECS


def seed_if_empty(db: Session) -> None:
    if db.get(AppSetting, 1) is None:
        db.add(AppSetting(id=1, simulation_speed=1.0, paused=False))
    machine_count = db.scalar(select(func.count()).select_from(Machine)) or 0
    if machine_count > 0:
        return

    now = now_ts()
    rng = random.Random(7)
    for spec in MACHINE_SPECS:
        machine = Machine(
            id=str(spec["id"]),
            name=str(spec["name"]),
            machine_type=str(spec["machine_type"]),
            description=str(spec["description"]),
            status="RUNNING",
            ideal_cycle_time=float(spec["ideal_cycle_time"]),
            defect_rate=float(spec["defect_rate"]),
            temp_min=float(spec["temp_min"]),
            temp_max=float(spec["temp_max"]),
            temp_warning=float(spec["temp_warning"]),
            temp_critical=float(spec["temp_critical"]),
            vib_min=float(spec["vib_min"]),
            vib_max=float(spec["vib_max"]),
            vib_warning=float(spec["vib_warning"]),
            vib_critical=float(spec["vib_critical"]),
            current_min=float(spec["current_min"]),
            current_max=float(spec["current_max"]),
            current_warning=float(spec["current_warning"]),
            current_critical=float(spec["current_critical"]),
            active_scenario=None,
            cycle_accumulator=0.0,
            production_count=0,
            good_count=0,
            defect_count=0,
            running_seconds=0.0,
            idle_seconds=0.0,
            fault_seconds=0.0,
            stopped_seconds=0.0,
            stop_count=2,
            last_update=now,
        )
        machine.temperature = (machine.temp_min + machine.temp_max) / 2
        machine.vibration = (machine.vib_min + machine.vib_max) / 2
        machine.motor_current = (machine.current_min + machine.current_max) / 2
        db.add(machine)
        db.flush()
        _seed_samples(db, machine, now, rng)
        _seed_status_events(db, machine, now)
    _seed_alarms(db, now)


def _seed_samples(db: Session, machine: Machine, now: float, rng: random.Random) -> None:
    pattern = (["RUNNING"] * 28) + (["IDLE"] * 5) + (["STOPPED"] * 3) + (["FAULT"] * 2)
    total = len(pattern)
    for index, status in enumerate(pattern):
        timestamp = now - (total - index) * 2.5
        temperature = rng.uniform(machine.temp_min, machine.temp_max)
        vibration = rng.uniform(machine.vib_min, machine.vib_max)
        current = rng.uniform(machine.current_min, machine.current_max)
        if status == "IDLE":
            current = machine.current_min * 0.45
        elif status == "STOPPED":
            temperature, vibration, current = 28.0, 0.08, 0.05
        elif status == "FAULT":
            temperature = machine.temp_max
            vibration = machine.vib_max
            current = 0.1
        produced = good = defect = 0
        if status == "RUNNING":
            produced = max(1, int(2.5 // machine.ideal_cycle_time))
            for _ in range(produced):
                if rng.random() < machine.defect_rate:
                    defect += 1
                else:
                    good += 1
            machine.running_seconds += 2.5
            machine.production_count += produced
            machine.good_count += good
            machine.defect_count += defect
        elif status == "IDLE":
            machine.idle_seconds += 2.5
        elif status == "FAULT":
            machine.fault_seconds += 2.5
        else:
            machine.stopped_seconds += 2.5
        db.add(
            MetricSample(
                machine_id=machine.id,
                timestamp=timestamp,
                status=status,
                temperature=round(temperature, 2),
                vibration=round(vibration, 3),
                motor_current=round(current, 2),
                dt_seconds=2.5,
                total_delta=produced,
                good_delta=good,
                defect_delta=defect,
            )
        )


def _seed_status_events(db: Session, machine: Machine, now: float) -> None:
    events = [
        (now - 95, "RUNNING", "Demo history started in the running state."),
        (now - 40, "IDLE", "Seeded idle interval for downtime reporting."),
        (now - 27, "STOPPED", "Seeded operator stop."),
        (now - 18, "FAULT", "Seeded fault interval. This historical fault is already cleared."),
        (now - 8, "RUNNING", "Demo machine returned to running before live simulation."),
    ]
    for timestamp, status, note in events:
        db.add(StatusEvent(machine_id=machine.id, timestamp=timestamp, status=status, note=note))


def _seed_alarms(db: Session, now: float) -> None:
    samples = [
        ("MCH-A", "EXCESSIVE_VIBRATION", "WARNING", "Historical vibration warning on Conveyor System. Already acknowledged."),
        ("MCH-B", "HIGH_TEMPERATURE", "CRITICAL", "Historical high-temperature alarm on Packaging Machine. Already acknowledged."),
        ("MCH-C", "MOTOR_OVERLOAD", "WARNING", "Historical motor current warning on Electric Motor. Already acknowledged."),
        ("MCH-D", "PROCESS_NOTE", "INFO", "Inspection Station completed a simulated warm-up check."),
    ]
    for machine_id, alarm_type, severity, description in samples:
        db.add(
            Alarm(
                machine_id=machine_id,
                alarm_type=alarm_type,
                severity=severity,
                description=description,
                timestamp=now - 3600,
                updated_at=now - 3500,
                acknowledged=True,
                acknowledged_at=now - 3400,
                active=False,
                cleared_at=now - 3300,
            )
        )
