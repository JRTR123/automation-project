"""Overall Equipment Effectiveness for simulated production time."""

from __future__ import annotations


def calculate_oee(
    running_seconds: float,
    idle_seconds: float,
    fault_seconds: float,
    stopped_seconds: float,
    total_count: int,
    good_count: int,
    ideal_cycle_time: float,
) -> dict[str, float]:
    """Return OEE factors in the range 0 to 1.

    Availability = operating time / planned production time
    Performance = (ideal cycle time * total count) / operating time
    Quality = good count / total count

    Planned production time is running + idle + fault + stopped time.
    Operating time is running time. Each factor is capped at 100% when
    combined into OEE. Raw performance is returned separately because a
    simulated rate can exceed the ideal cycle time.
    """
    running = max(running_seconds, 0.0)
    idle = max(idle_seconds, 0.0)
    fault = max(fault_seconds, 0.0)
    stopped = max(stopped_seconds, 0.0)
    planned = running + idle + fault + stopped
    availability = (running / planned) if planned > 0 else 0.0
    if running > 0 and total_count > 0 and ideal_cycle_time > 0:
        performance = (ideal_cycle_time * total_count) / running
    else:
        performance = 0.0
    quality = (good_count / total_count) if total_count > 0 else 0.0

    availability_used = _cap(availability)
    performance_used = _cap(performance)
    quality_used = _cap(quality)
    return {
        "availability": availability_used,
        "performance": performance_used,
        "quality": quality_used,
        "performance_raw": max(performance, 0.0),
        "oee": availability_used * performance_used * quality_used,
        "operating_seconds": running,
        "planned_seconds": planned,
        "downtime_seconds": fault + stopped,
    }


def _cap(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value
