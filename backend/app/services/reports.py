"""Report aggregates computed from stored samples and alarms."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timeutil import to_iso
from app.models.entities import Alarm, Machine, MetricSample
from app.services.oee import calculate_oee


def build_report(db: Session, start: float | None, end: float | None) -> dict:
    machines = list(db.scalars(select(Machine).order_by(Machine.id)).all())
    rows = []
    trends = []
    for machine in machines:
        samples = _samples(db, machine.id, start, end)
        alarms = _alarms(db, machine.id, start, end)
        running = sum(item.dt_seconds for item in samples if item.status == "RUNNING")
        idle = sum(item.dt_seconds for item in samples if item.status == "IDLE")
        fault = sum(item.dt_seconds for item in samples if item.status == "FAULT")
        stopped = sum(item.dt_seconds for item in samples if item.status == "STOPPED")
        total = sum(item.total_delta for item in samples)
        good = sum(item.good_delta for item in samples)
        defect = sum(item.defect_delta for item in samples)
        oee = calculate_oee(running, idle, fault, stopped, total, good, machine.ideal_cycle_time)
        rows.append(
            {
                "machine_id": machine.id,
                "machine_name": machine.name,
                "running_seconds": round(running, 1),
                "idle_seconds": round(idle, 1),
                "downtime_seconds": round(fault + stopped, 1),
                "fault_seconds": round(fault, 1),
                "stopped_seconds": round(stopped, 1),
                "alarm_count": len(alarms),
                "warning_count": sum(1 for alarm in alarms if alarm.severity == "WARNING"),
                "critical_count": sum(1 for alarm in alarms if alarm.severity == "CRITICAL"),
                "info_count": sum(1 for alarm in alarms if alarm.severity == "INFO"),
                "production_count": total,
                "good_count": good,
                "defect_count": defect,
                "oee": oee["oee"],
                "availability": oee["availability"],
                "performance": oee["performance"],
                "quality": oee["quality"],
            }
        )
        points = _downsample(samples, 120)
        trends.append(
            {
                "machine_id": machine.id,
                "machine_name": machine.name,
                "points": [
                    {
                        "timestamp": to_iso(point.timestamp),
                        "temperature": round(point.temperature, 2),
                        "vibration": round(point.vibration, 3),
                        "motor_current": round(point.motor_current, 2),
                    }
                    for point in points
                ],
            }
        )
    return {"machines": rows, "trends": trends}


def _samples(db: Session, machine_id: str, start: float | None, end: float | None) -> list[MetricSample]:
    query = select(MetricSample).where(MetricSample.machine_id == machine_id)
    if start is not None:
        query = query.where(MetricSample.timestamp >= start)
    if end is not None:
        query = query.where(MetricSample.timestamp <= end)
    query = query.order_by(MetricSample.timestamp.asc())
    return list(db.scalars(query).all())


def _alarms(db: Session, machine_id: str, start: float | None, end: float | None) -> list[Alarm]:
    query = select(Alarm).where(Alarm.machine_id == machine_id)
    if start is not None:
        query = query.where(Alarm.timestamp >= start)
    if end is not None:
        query = query.where(Alarm.timestamp <= end)
    return list(db.scalars(query).all())


def _downsample(samples: list[MetricSample], max_points: int) -> list[MetricSample]:
    if len(samples) <= max_points:
        return samples
    step = len(samples) / max_points
    return [samples[int(index * step)] for index in range(max_points)]
