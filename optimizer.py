from dataclasses import dataclass
from typing import List

@dataclass
class Stop:
    """Simple representation of a stop used for optimization."""
    facility: str
    drive_time: float

@dataclass
class Shift:
    stops: List[Stop]
    total_hours: float


def generate_shifts(stops: List[Stop], min_hours: float = 10.0, max_hours: float = 12.0) -> List[Shift]:
    """Group stops into shifts while keeping total_hours within min and max bounds."""
    shifts: List[Shift] = []
    current: List[Stop] = []
    hours = 0.0

    for idx, stop in enumerate(stops):
        if current and hours + stop.drive_time > max_hours:
            shifts.append(Shift(stops=current, total_hours=hours))
            current = []
            hours = 0.0
        current.append(stop)
        hours += stop.drive_time
        if hours >= max_hours:
            shifts.append(Shift(stops=current, total_hours=hours))
            current = []
            hours = 0.0

    if current:
        shifts.append(Shift(stops=current, total_hours=hours))

    # If the last shift ended up under min_hours and there is more than one shift,
    # try to balance by moving a stop from the previous shift.
    if len(shifts) >= 2 and shifts[-1].total_hours < min_hours:
        prev = shifts[-2]
        last = shifts[-1]
        if prev.stops:
            moved = prev.stops.pop()
            prev.total_hours -= moved.drive_time
            last.stops.insert(0, moved)
            last.total_hours += moved.drive_time
    return shifts
