"""Persistent tables for machines, samples, alarms, and settings."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    machine_type: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default="RUNNING")
    temperature: Mapped[float] = mapped_column(Float, default=40.0)
    vibration: Mapped[float] = mapped_column(Float, default=1.0)
    motor_current: Mapped[float] = mapped_column(Float, default=4.0)
    production_count: Mapped[int] = mapped_column(Integer, default=0)
    good_count: Mapped[int] = mapped_column(Integer, default=0)
    defect_count: Mapped[int] = mapped_column(Integer, default=0)
    running_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    idle_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    fault_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    stopped_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    stop_count: Mapped[int] = mapped_column(Integer, default=0)
    ideal_cycle_time: Mapped[float] = mapped_column(Float, default=2.0)
    defect_rate: Mapped[float] = mapped_column(Float, default=0.02)
    cycle_accumulator: Mapped[float] = mapped_column(Float, default=0.0)
    temp_min: Mapped[float] = mapped_column(Float)
    temp_max: Mapped[float] = mapped_column(Float)
    temp_warning: Mapped[float] = mapped_column(Float)
    temp_critical: Mapped[float] = mapped_column(Float)
    vib_min: Mapped[float] = mapped_column(Float)
    vib_max: Mapped[float] = mapped_column(Float)
    vib_warning: Mapped[float] = mapped_column(Float)
    vib_critical: Mapped[float] = mapped_column(Float)
    current_min: Mapped[float] = mapped_column(Float)
    current_max: Mapped[float] = mapped_column(Float)
    current_warning: Mapped[float] = mapped_column(Float)
    current_critical: Mapped[float] = mapped_column(Float)
    active_scenario: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_update: Mapped[float] = mapped_column(Float, default=0.0)


class MetricSample(Base):
    __tablename__ = "metric_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    status: Mapped[str] = mapped_column(String(16))
    temperature: Mapped[float] = mapped_column(Float)
    vibration: Mapped[float] = mapped_column(Float)
    motor_current: Mapped[float] = mapped_column(Float)
    dt_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    total_delta: Mapped[int] = mapped_column(Integer, default=0)
    good_delta: Mapped[int] = mapped_column(Integer, default=0)
    defect_delta: Mapped[int] = mapped_column(Integer, default=0)


class Alarm(Base):
    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    alarm_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(String(500))
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    updated_at: Mapped[float] = mapped_column(Float)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    cleared_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class StatusEvent(Base):
    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    status: Mapped[str] = mapped_column(String(16))
    note: Mapped[str] = mapped_column(String(300))


class AppSetting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_speed: Mapped[float] = mapped_column(Float, default=1.0)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
