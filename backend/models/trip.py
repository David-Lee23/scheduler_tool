from dataclasses import dataclass
import datetime as dt

@dataclass
class Trip:
    id: str
    contract_id: str
    trip_date: dt.date
    start_time: dt.time
    end_time: dt.time
    start_location: str
    end_location: str
    distance: float
    duration: float
    required_driver_class: str
