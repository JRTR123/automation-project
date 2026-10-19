"""Sensor threshold detection, duplicate prevention, and acknowledgment."""

from sqlalchemy import select

from app.models.entities import Alarm, Machine
from app.services.alarms import acknowledge_alarm, evaluate_sensor_alarms


def _active(db_session, machine_id: str, alarm_type: str) -> list[Alarm]:
    return list(
        db_session.scalars(
            select(Alarm).where(
                Alarm.machine_id == machine_id,
                Alarm.alarm_type == alarm_type,
                Alarm.active.is_(True),
            )
        ).all()
    )


def test_critical_threshold_creates_one_alarm(db_session):
    machine = db_session.get(Machine, "MCH-A")
    assert machine is not None
    machine.temperature = machine.temp_critical + 1
    evaluate_sensor_alarms(db_session, machine)
    evaluate_sensor_alarms(db_session, machine)
    rows = _active(db_session, "MCH-A", "HIGH_TEMPERATURE")
    assert len(rows) == 1
    assert rows[0].severity == "CRITICAL"
    assert "Conveyor System" in rows[0].description


def test_warning_escalates_without_a_second_alarm(db_session):
    machine = db_session.get(Machine, "MCH-B")
    assert machine is not None
    machine.temperature = machine.temp_warning + 0.4
    evaluate_sensor_alarms(db_session, machine)
    warning = _active(db_session, "MCH-B", "HIGH_TEMPERATURE")
    assert len(warning) == 1
    assert warning[0].severity == "WARNING"
    machine.temperature = machine.temp_critical + 0.4
    evaluate_sensor_alarms(db_session, machine)
    critical = _active(db_session, "MCH-B", "HIGH_TEMPERATURE")
    assert len(critical) == 1
    assert critical[0].id == warning[0].id
    assert critical[0].severity == "CRITICAL"


def test_returning_to_normal_clears_without_deleting_history(db_session):
    machine = db_session.get(Machine, "MCH-C")
    assert machine is not None
    machine.motor_current = machine.current_warning + 0.2
    evaluate_sensor_alarms(db_session, machine)
    alarm = _active(db_session, "MCH-C", "MOTOR_OVERLOAD")[0]
    machine.motor_current = machine.current_min
    evaluate_sensor_alarms(db_session, machine)
    alarm_id = alarm.id
    db_session.flush()
    db_session.expire_all()
    stored = db_session.get(Alarm, alarm_id)
    assert stored is not None
    assert stored.active is False
    assert stored.cleared_at is not None


def test_acknowledge_records_time_and_does_not_change_machine_status(db_session):
    machine = db_session.get(Machine, "MCH-A")
    assert machine is not None
    machine.vibration = machine.vib_critical + 0.2
    machine.status = "RUNNING"
    evaluate_sensor_alarms(db_session, machine)
    alarm = _active(db_session, "MCH-A", "EXCESSIVE_VIBRATION")[0]
    acknowledge_alarm(db_session, alarm.id)
    assert alarm.acknowledged is True
    assert alarm.acknowledged_at is not None
    assert machine.status == "RUNNING"
    assert alarm.active is True
