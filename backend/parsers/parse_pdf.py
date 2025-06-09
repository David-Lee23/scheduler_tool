"""PDF trip manifest parser."""

from __future__ import annotations

import re
import uuid
import datetime as dt
from typing import List, Optional

import pdfplumber

from models.trip import Trip

# Regular expressions used for parsing
_CONTRACT_RE = re.compile(r"HCR#\s+\S+\s+(\d{3}[A-Z]\d)", re.I)
_TRIP_SPLIT_RE = re.compile(r"(?=^\s*Trip\s+ID\s+\d+)", re.M)
_STOP_ROW_RE = re.compile(r"\s*(\d+)\s+([0-9:]{4,5})?\s+([0-9:]{4,5})?\s+(.+?)\s{2,}\d")
_SUMMARY_RE = re.compile(r"Trip\s+Miles\s+.*?([\d.]+)\s+.*?Trip\s+Hrs\s+.*?([\d.]+)", re.S)
_DATE_HEADER_RE = re.compile(r"Schedule\s*Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})", re.I)
_DATE_IN_LINE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")


def _extract_schedule_date(text: str) -> Optional[dt.date]:
    match = _DATE_HEADER_RE.search(text)
    if match:
        try:
            return dt.datetime.strptime(match.group(1), "%m/%d/%Y").date()
        except ValueError:
            return None
    return None


def _parse_trip_block(
    block: str, contract_id: str, page_num: int, page_date: Optional[dt.date]
) -> Optional[Trip]:
    lines = block.splitlines()
    stops: List[tuple[Optional[str], Optional[str], str, Optional[dt.date]]] = []
    trip_date: Optional[dt.date] = None

    for line in lines:
        stop_match = _STOP_ROW_RE.match(line)
        if stop_match:
            arrive = stop_match.group(2)
            depart = stop_match.group(3)
            location = stop_match.group(4).strip()
            date_match = _DATE_IN_LINE_RE.search(line)
            if trip_date is None and date_match:
                try:
                    trip_date = dt.datetime.strptime(date_match.group(1), "%m/%d/%Y").date()
                except ValueError:
                    pass
            stops.append((arrive, depart, location, trip_date))

    if not stops:
        return None

    summary_match = _SUMMARY_RE.search(block)
    if summary_match is None:
        raise ValueError(f"Missing summary line with miles/hours on page {page_num}")

    if trip_date is None:
        trip_date = page_date
    if trip_date is None:
        raise ValueError(f"Could not determine trip date on page {page_num}")

    try:
        distance = float(summary_match.group(1))
        duration = float(summary_match.group(2))
        start_time_str = stops[0][1] or stops[0][0]
        end_time_str = stops[-1][1] or stops[-1][0]
        start_time = dt.datetime.strptime(start_time_str, "%H:%M").time()
        end_time = dt.datetime.strptime(end_time_str, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Failed to convert numeric values on page {page_num}") from exc

    return Trip(
        id=uuid.uuid4().hex,
        contract_id=contract_id,
        trip_date=trip_date,
        start_time=start_time,
        end_time=end_time,
        start_location=stops[0][2],
        end_location=stops[-1][2],
        distance=distance,
        duration=duration,
        required_driver_class="",
    )


def parse_pdf(pdf_path: str) -> List[Trip]:
    """Extract all trips from the contract PDF located at ``pdf_path``.

    Raise ``ValueError`` when the contract header is missing, when no trip
    blocks are found, when a trip block lacks its summary line, or when any
    numeric conversion fails.
    """

    trips: List[Trip] = []
    contract_id: Optional[str] = None
    found_block = False

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if contract_id is None:
                contract_match = _CONTRACT_RE.search(text)
                if contract_match:
                    contract_id = contract_match.group(1)
            page_date = _extract_schedule_date(text)

            for block in _TRIP_SPLIT_RE.split(text):
                if not block.lstrip().startswith("Trip ID"):
                    continue
                found_block = True
                trip = _parse_trip_block(block, contract_id or "", page_num, page_date)
                if trip:
                    trips.append(trip)

    if contract_id is None:
        raise ValueError("Contract ID header not found in document")
    if not found_block:
        raise ValueError("No Trip blocks found in document")

    return trips
