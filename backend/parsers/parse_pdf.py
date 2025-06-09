"""Stub parser that converts a contract PDF into Trip objects."""
from pathlib import Path
from typing import List
from models.trip import Trip
import uuid
import datetime as dt

def parse_pdf(pdf_path: str) -> List[Trip]:
    print(f"[parse_pdf] Parsing {pdf_path} (stub).")
    trip = Trip(
        id=str(uuid.uuid4()),
        contract_id="CONTRACT_STUB",
        trip_date=dt.date.today(),
        start_time=dt.time(8, 0),
        end_time=dt.time(10, 0),
        start_location="Depot A",
        end_location="Depot B",
        distance=120.0,
        duration=2.0,
        required_driver_class="A"
    )
    return [trip]
