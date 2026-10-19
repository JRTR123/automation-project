"""REST routes for machines, alarms, reports, settings, and simulation."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.errors import AppError
from app.core.timeutil import parse_iso, to_iso
from app.models.entities import Alarm, Machine, MetricSample, StatusEvent
from app.schemas import (
    ActionOut,
    AlarmOut,
    HealthOut,
    HistoryOut,
    MachineOut,
    MachineSettingsOut,
    ProductionMachineOut,
    ProductionSummaryOut,
    ReadingOut,
    ReportSummaryOut,
    ScenarioIn,
    SettingsIn,
    SettingsOut,
    SimulationOut,
    StatusEventOut,
)
from app.services import alarms, machines, reports
from app.services.catalog import DISCLAIMER
from app.services.oee import calculate_oee
from app.services.simulator import engine

router = APIRouter()


def _write(db: Session, action: Callable[[], object]):
    with engine.write_lock:
        try:
            result = action()
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise


@router.get("/health", response_model=HealthOut, tags=["health"])
def health(db: Session = Depends(get_db)) -> HealthOut:
    row = machines.get_settings_row(db)
    return HealthOut(
        status="ok",
        simulation=engine.state(),
        simulation_speed=row.simulation_speed,
        database="sqlite",
    )


@router.get("/machines", response_model=list[MachineOut], tags=["machines"])
def get_machines(db: Session = Depends(get_db)) -> list[MachineOut]:
    return [machines.serialize_machine(db, machine) for machine in machines.list_machines(db)]


@router.get("/machines/{machine_id}", response_model=MachineOut, tags=["machines"])
def get_machine(machine_id: str, db: Session = Depends(get_db)) -> MachineOut:
    return machines.serialize_machine(db, machines.get_machine(db, machine_id))


@router.get("/machines/{machine_id}/history", response_model=HistoryOut, tags=["machines"])
def get_history(
    machine_id: str,
    limit: int = Query(default=80, ge=1, le=500),
    db: Session = Depends(get_db),
) -> HistoryOut:
    machine = machines.get_machine(db, machine_id)
    samples = list(
        db.scalars(
            select(MetricSample)
            .where(MetricSample.machine_id == machine_id)
            .order_by(MetricSample.timestamp.desc())
            .limit(limit)
        ).all()
    )
    samples.reverse()
    events = list(
        db.scalars(
            select(StatusEvent)
            .where(StatusEvent.machine_id == machine_id)
            .order_by(StatusEvent.timestamp.desc())
            .limit(20)
        ).all()
    )
    recent_alarms = list(
        db.scalars(
            select(Alarm).where(Alarm.machine_id == machine_id).order_by(Alarm.timestamp.desc()).limit(10)
        ).all()
    )
    return HistoryOut(
        machine=machines.serialize_machine(db, machine),
        readings=[
            ReadingOut(
                timestamp=to_iso(sample.timestamp) or "",
                status=sample.status,
                temperature=round(sample.temperature, 2),
                vibration=round(sample.vibration, 3),
                motor_current=round(sample.motor_current, 2),
            )
            for sample in samples
        ],
        status_history=[
            StatusEventOut(timestamp=to_iso(event.timestamp) or "", status=event.status, note=event.note)
            for event in events
        ],
        alarms=[AlarmOut(**alarms.serialize_alarm(alarm, machine.name)) for alarm in recent_alarms],
    )


@router.post("/machines/{machine_id}/start", response_model=ActionOut, tags=["machines"])
def start_machine(machine_id: str, db: Session = Depends(get_db)) -> ActionOut:
    def action() -> ActionOut:
        message, machine = machines.start_machine(db, machine_id)
        return ActionOut(message=message, machine=machines.serialize_machine(db, machine))

    return _write(db, action)


@router.post("/machines/{machine_id}/stop", response_model=ActionOut, tags=["machines"])
def stop_machine(machine_id: str, db: Session = Depends(get_db)) -> ActionOut:
    def action() -> ActionOut:
        message, machine = machines.stop_machine(db, machine_id)
        return ActionOut(message=message, machine=machines.serialize_machine(db, machine))

    return _write(db, action)


@router.post("/machines/{machine_id}/reset", response_model=ActionOut, tags=["machines"])
def reset_machine(machine_id: str, db: Session = Depends(get_db)) -> ActionOut:
    def action() -> ActionOut:
        message, machine = machines.reset_machine(db, machine_id)
        return ActionOut(message=message, machine=machines.serialize_machine(db, machine))

    return _write(db, action)


@router.get("/alarms", response_model=list[AlarmOut], tags=["alarms"])
def get_alarms(
    machine_id: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    db: Session = Depends(get_db),
) -> list[AlarmOut]:
    return [_alarm_out(db, alarm) for alarm in _query_alarms(db, machine_id, severity, acknowledged)]


@router.get("/alarms/export", tags=["alarms"])
def export_alarms(
    machine_id: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    rows = _query_alarms(db, machine_id, severity, acknowledged)
    names = {machine.id: machine.name for machine in machines.list_machines(db)}
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "machine_id",
            "machine_name",
            "alarm_type",
            "severity",
            "description",
            "timestamp",
            "acknowledged",
            "acknowledged_at",
            "active",
            "cleared_at",
        ]
    )
    for alarm in rows:
        writer.writerow(
            [
                alarm.id,
                alarm.machine_id,
                names.get(alarm.machine_id, alarm.machine_id),
                alarm.alarm_type,
                alarm.severity,
                alarm.description,
                to_iso(alarm.timestamp),
                alarm.acknowledged,
                to_iso(alarm.acknowledged_at) or "",
                alarm.active,
                to_iso(alarm.cleared_at) or "",
            ]
        )
    return _csv(buffer.getvalue(), "alarm-history.csv")


@router.post("/alarms/{alarm_id}/acknowledge", response_model=AlarmOut, tags=["alarms"])
def acknowledge(alarm_id: int, db: Session = Depends(get_db)) -> AlarmOut:
    def action() -> AlarmOut:
        alarm = alarms.acknowledge_alarm(db, alarm_id)
        return _alarm_out(db, alarm)

    return _write(db, action)


@router.get("/production/summary", response_model=ProductionSummaryOut, tags=["production"])
def production_summary(db: Session = Depends(get_db)) -> ProductionSummaryOut:
    machine_rows = [_production_row(machine) for machine in machines.list_machines(db)]
    return ProductionSummaryOut(
        simulated=True,
        disclaimer=DISCLAIMER,
        formula={
            "oee": "Availability × Performance × Quality",
            "availability": "Operating time / planned production time",
            "performance": "(Ideal cycle time × total count) / operating time",
            "quality": "Good count / total count",
            "planned_production_time": "Running + idle + fault + stopped time",
            "operating_time": "Running time",
            "downtime": "Fault time + stopped time",
        },
        totals=_combine_totals(machine_rows),
        machines=machine_rows,
    )


@router.get("/production/export", tags=["production"])
def export_production(db: Session = Depends(get_db)) -> StreamingResponse:
    summary = production_summary(db)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "machine_id",
            "machine_name",
            "status",
            "production_count",
            "good_count",
            "defect_count",
            "running_seconds",
            "idle_seconds",
            "fault_seconds",
            "stopped_seconds",
            "downtime_seconds",
            "stop_count",
            "availability",
            "performance",
            "quality",
            "oee",
        ]
    )
    for row in [summary.totals, *summary.machines]:
        writer.writerow(
            [
                row.machine_id,
                row.machine_name,
                row.status,
                row.production_count,
                row.good_count,
                row.defect_count,
                row.running_seconds,
                row.idle_seconds,
                row.fault_seconds,
                row.stopped_seconds,
                row.downtime_seconds,
                row.stop_count,
                f"{row.oee.availability:.4f}",
                f"{row.oee.performance:.4f}",
                f"{row.oee.quality:.4f}",
                f"{row.oee.oee:.4f}",
            ]
        )
    return _csv(buffer.getvalue(), "production-summary.csv")


@router.get("/reports/summary", response_model=ReportSummaryOut, tags=["reports"])
def report_summary(
    from_time: str | None = Query(default=None, alias="from"),
    to_time: str | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
) -> ReportSummaryOut:
    start, end = _range(from_time, to_time)
    payload = reports.build_report(db, start, end)
    return ReportSummaryOut(
        simulated=True,
        disclaimer=DISCLAIMER,
        from_timestamp=to_iso(start),
        to_timestamp=to_iso(end),
        machines=payload["machines"],
        trends=payload["trends"],
    )


@router.get("/settings", response_model=SettingsOut, tags=["settings"])
def get_settings(db: Session = Depends(get_db)) -> SettingsOut:
    return _settings_out(db)


@router.put("/settings", response_model=SettingsOut, tags=["settings"])
def put_settings(body: SettingsIn, db: Session = Depends(get_db)) -> SettingsOut:
    def action() -> SettingsOut:
        machines.update_thresholds(db, body.simulation_speed, body.machines)
        return _settings_out(db)

    return _write(db, action)


@router.post("/simulation/start", response_model=SimulationOut, tags=["simulation"])
def simulation_start(db: Session = Depends(get_db)) -> SimulationOut:
    message = engine.start()
    return _simulation_out(db, message)


@router.post("/simulation/pause", response_model=SimulationOut, tags=["simulation"])
def simulation_pause(db: Session = Depends(get_db)) -> SimulationOut:
    message = engine.pause()
    return _simulation_out(db, message)


@router.post("/simulation/resume", response_model=SimulationOut, tags=["simulation"])
def simulation_resume(db: Session = Depends(get_db)) -> SimulationOut:
    message = engine.resume()
    return _simulation_out(db, message)


@router.post("/simulation/scenarios/{scenario_name}", response_model=ActionOut, tags=["simulation"])
def simulation_scenario(scenario_name: str, body: ScenarioIn, db: Session = Depends(get_db)) -> ActionOut:
    def action() -> ActionOut:
        message, machine = engine.trigger(db, scenario_name, body.machine_id)
        return ActionOut(message=message, machine=machines.serialize_machine(db, machine))

    return _write(db, action)


def _query_alarms(
    db: Session,
    machine_id: str | None,
    severity: str | None,
    acknowledged: bool | None,
) -> list[Alarm]:
    if severity is not None and severity not in {"INFO", "WARNING", "CRITICAL"}:
        raise AppError("Severity must be INFO, WARNING, or CRITICAL.", 422)
    query = select(Alarm)
    if machine_id:
        query = query.where(Alarm.machine_id == machine_id)
    if severity:
        query = query.where(Alarm.severity == severity)
    if acknowledged is not None:
        query = query.where(Alarm.acknowledged.is_(acknowledged))
    return list(db.scalars(query.order_by(Alarm.timestamp.desc()).limit(500)).all())


def _alarm_out(db: Session, alarm: Alarm) -> AlarmOut:
    machine = db.get(Machine, alarm.machine_id)
    name = machine.name if machine else alarm.machine_id
    return AlarmOut(**alarms.serialize_alarm(alarm, name))


def _production_row(machine: Machine) -> ProductionMachineOut:
    oee = calculate_oee(
        machine.running_seconds,
        machine.idle_seconds,
        machine.fault_seconds,
        machine.stopped_seconds,
        machine.production_count,
        machine.good_count,
        machine.ideal_cycle_time,
    )
    return ProductionMachineOut(
        machine_id=machine.id,
        machine_name=machine.name,
        status=machine.status,
        production_count=machine.production_count,
        good_count=machine.good_count,
        defect_count=machine.defect_count,
        running_seconds=round(machine.running_seconds, 1),
        idle_seconds=round(machine.idle_seconds, 1),
        fault_seconds=round(machine.fault_seconds, 1),
        stopped_seconds=round(machine.stopped_seconds, 1),
        downtime_seconds=round(machine.fault_seconds + machine.stopped_seconds, 1),
        stop_count=machine.stop_count,
        ideal_cycle_time=machine.ideal_cycle_time,
        oee=oee,
    )


def _combine_totals(rows: list[ProductionMachineOut]) -> ProductionMachineOut:
    running = sum(row.running_seconds for row in rows)
    idle = sum(row.idle_seconds for row in rows)
    fault = sum(row.fault_seconds for row in rows)
    stopped = sum(row.stopped_seconds for row in rows)
    total = sum(row.production_count for row in rows)
    good = sum(row.good_count for row in rows)
    if total > 0:
        ideal = sum(row.ideal_cycle_time * row.production_count for row in rows) / total
    else:
        ideal = 0.0
    oee = calculate_oee(running, idle, fault, stopped, total, good, ideal)
    return ProductionMachineOut(
        machine_id="ALL",
        machine_name="All machines",
        status="MIXED",
        production_count=total,
        good_count=good,
        defect_count=sum(row.defect_count for row in rows),
        running_seconds=round(running, 1),
        idle_seconds=round(idle, 1),
        fault_seconds=round(fault, 1),
        stopped_seconds=round(stopped, 1),
        downtime_seconds=round(fault + stopped, 1),
        stop_count=sum(row.stop_count for row in rows),
        ideal_cycle_time=round(ideal, 3),
        oee=oee,
    )


def _settings_out(db: Session) -> SettingsOut:
    row = machines.get_settings_row(db)
    return SettingsOut(
        simulation_speed=row.simulation_speed,
        tick_interval_seconds=round(machines.tick_interval(row.simulation_speed), 2),
        simulation=engine.state(),
        machines=[
            MachineSettingsOut(
                machine_id=machine.id,
                name=machine.name,
                temp_min=machine.temp_min,
                temp_max=machine.temp_max,
                temp_warning=machine.temp_warning,
                temp_critical=machine.temp_critical,
                vib_min=machine.vib_min,
                vib_max=machine.vib_max,
                vib_warning=machine.vib_warning,
                vib_critical=machine.vib_critical,
                current_min=machine.current_min,
                current_max=machine.current_max,
                current_warning=machine.current_warning,
                current_critical=machine.current_critical,
            )
            for machine in machines.list_machines(db)
        ],
    )


def _simulation_out(db: Session, message: str) -> SimulationOut:
    row = machines.get_settings_row(db)
    return SimulationOut(state=engine.state(), message=message, simulation_speed=row.simulation_speed)


def _range(from_time: str | None, to_time: str | None) -> tuple[float | None, float | None]:
    try:
        start = parse_iso(from_time)
        end = parse_iso(to_time)
    except ValueError as exc:
        raise AppError(str(exc), 422) from exc
    if start is not None and end is not None and start > end:
        raise AppError("The start time must be earlier than the end time.", 422)
    return start, end


def _csv(content: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
