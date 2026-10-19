"""Create and update alarms without duplicating an active condition."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import now_ts, to_iso
from app.models.entities import Alarm, Machine

SEVERITY_RANK = {"INFO": 1, "WARNING": 2, "CRITICAL": 3}
HYSTERESIS = 0.97

SENSOR_RULES = (
    ("temperature", "HIGH_TEMPERATURE", "Temperature", "°C", "temp_warning", "temp_critical"),
    ("vibration", "EXCESSIVE_VIBRATION", "Vibration", "mm/s", "vib_warning", "vib_critical"),
    ("motor_current", "MOTOR_OVERLOAD", "Motor current", "A", "current_warning", "current_critical"),
)


def active_alarm(db: Session, machine_id: str, alarm_type: str) -> Alarm | None:
    return db.scalar(
        select(Alarm)
        .where(
            Alarm.machine_id == machine_id,
            Alarm.alarm_type == alarm_type,
            Alarm.active.is_(True),
        )
        .order_by(Alarm.id.desc())
    )


def active_alarm_count(db: Session, machine_id: str) -> int:
    rows = db.scalars(
        select(Alarm).where(Alarm.machine_id == machine_id, Alarm.active.is_(True))
    ).all()
    return len(rows)


def evaluate_sensor_alarms(db: Session, machine: Machine, timestamp: float | None = None) -> None:
    """Open, escalate, or clear sensor alarms from the current reading."""
    moment = timestamp if timestamp is not None else now_ts()
    for attr, alarm_type, label, unit, warn_attr, crit_attr in SENSOR_RULES:
        value = float(getattr(machine, attr))
        warning = float(getattr(machine, warn_attr))
        critical = float(getattr(machine, crit_attr))
        existing = active_alarm(db, machine.id, alarm_type)
        if value >= warning:
            severity = "CRITICAL" if value >= critical else "WARNING"
            limit = critical if severity == "CRITICAL" else warning
            description = (
                f"{label} {value:.2f} {unit} exceeded the {severity.lower()} threshold "
                f"of {limit:.2f} {unit} on {machine.name}."
            )
            if existing is None:
                db.add(
                    Alarm(
                        machine_id=machine.id,
                        alarm_type=alarm_type,
                        severity=severity,
                        description=description,
                        timestamp=moment,
                        updated_at=moment,
                        acknowledged=False,
                        acknowledged_at=None,
                        active=True,
                        cleared_at=None,
                    )
                )
            elif SEVERITY_RANK[severity] > SEVERITY_RANK.get(existing.severity, 0):
                existing.severity = severity
                existing.description = description
                existing.updated_at = moment
        elif existing is not None and value < warning * HYSTERESIS:
            existing.active = False
            existing.cleared_at = moment
            existing.updated_at = moment


def ensure_fault_alarm(db: Session, machine: Machine, timestamp: float | None = None) -> Alarm:
    moment = timestamp if timestamp is not None else now_ts()
    existing = active_alarm(db, machine.id, "MACHINE_FAULT")
    if existing is not None:
        return existing
    alarm = Alarm(
        machine_id=machine.id,
        alarm_type="MACHINE_FAULT",
        severity="CRITICAL",
        description=(
            f"Machine fault: {machine.name} ({machine.id}) has stopped. "
            "Acknowledge the alarm to record that an operator has seen it. "
            "Use Reset machine to clear the fault and return the machine to IDLE."
        ),
        timestamp=moment,
        updated_at=moment,
        acknowledged=False,
        acknowledged_at=None,
        active=True,
        cleared_at=None,
    )
    db.add(alarm)
    return alarm


def deactivate_machine_alarms(db: Session, machine: Machine, timestamp: float | None = None) -> None:
    """Mark active alarms cleared without acknowledging them."""
    moment = timestamp if timestamp is not None else now_ts()
    alarms = db.scalars(
        select(Alarm).where(Alarm.machine_id == machine.id, Alarm.active.is_(True))
    ).all()
    for alarm in alarms:
        alarm.active = False
        alarm.cleared_at = moment
        alarm.updated_at = moment


def record_info(db: Session, machine: Machine, alarm_type: str, description: str, timestamp: float) -> None:
    db.add(
        Alarm(
            machine_id=machine.id,
            alarm_type=alarm_type,
            severity="INFO",
            description=description,
            timestamp=timestamp,
            updated_at=timestamp,
            acknowledged=False,
            acknowledged_at=None,
            active=False,
            cleared_at=timestamp,
        )
    )


def acknowledge_alarm(db: Session, alarm_id: int) -> Alarm:
    alarm = db.get(Alarm, alarm_id)
    if alarm is None:
        raise AppError(f"Alarm {alarm_id} was not found.", 404)
    if not alarm.acknowledged:
        alarm.acknowledged = True
        alarm.acknowledged_at = now_ts()
        alarm.updated_at = alarm.acknowledged_at
    return alarm


def serialize_alarm(alarm: Alarm, machine_name: str) -> dict:
    return {
        "id": alarm.id,
        "machine_id": alarm.machine_id,
        "machine_name": machine_name,
        "alarm_type": alarm.alarm_type,
        "severity": alarm.severity,
        "description": alarm.description,
        "timestamp": to_iso(alarm.timestamp),
        "updated_at": to_iso(alarm.updated_at),
        "acknowledged": alarm.acknowledged,
        "acknowledged_at": to_iso(alarm.acknowledged_at),
        "active": alarm.active,
        "cleared_at": to_iso(alarm.cleared_at),
    }
