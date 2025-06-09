from dataclasses import dataclass
from typing import List
from models.trip import Trip
import datetime as dt

@dataclass
class DriverShift:
    id: str
    driver_id: str
    shift_date: dt.date
    trips: List[Trip]
    total_hours: float
    total_miles: float
