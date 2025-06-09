from dataclasses import dataclass

@dataclass
class Driver:
    id: str
    name: str
    driver_class: str
    max_hours_per_day: int
    home_base: str
