"""PDF trip extraction utilities."""

from pathlib import Path
import uuid
import datetime as dt
from typing import List
import re

import pdfplumber

from models.trip import Trip


def _parse_header(lines: List[str], page_num: int) -> str:
    """Find the contract ID within the first few lines."""
    for line in lines[:5]:
        if line.startswith("Contract:"):
            match = re.search(r"Contract:\s*(\S+)", line)
            if match:
                return match.group(1)
    raise ValueError(f"Missing contract header on page {page_num}")


def parse_pdf(pdf_path: str) -> List[Trip]:
    """Extract trips from a contract PDF.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        A list of ``Trip`` objects representing every trip row found.

    Raises:
        ValueError: If required headers or numeric fields are missing or if
            no trip rows could be parsed.
    """
    path = Path(pdf_path)
    trips: List[Trip] = []

    with pdfplumber.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            contract_id = _parse_header(lines, page_num)

            header_idx = None
            for i, line in enumerate(lines):
                if re.search(r"Trip\s*Date", line, re.I):
                    header_idx = i
                    break
            if header_idx is not None:
                data_lines = lines[header_idx + 1 :]
            else:
                data_lines = lines

            for line in data_lines:
                parts = re.split(r"\s{2,}", line.strip())
                if len(parts) < 8:
                    continue
                trip_date_s, start_s, end_s, from_loc, to_loc, miles_s, hours_s, class_s = parts[:8]
                try:
                    trip_date = dt.datetime.strptime(trip_date_s, "%m/%d/%Y").date()
                    start_time = dt.datetime.strptime(start_s, "%H:%M").time()
                    end_time = dt.datetime.strptime(end_s, "%H:%M").time()
                    distance = float(miles_s)
                    duration = float(hours_s)
                except ValueError as exc:
                    raise ValueError(f"Failed to parse numeric field on page {page_num}: {line}") from exc

                trip = Trip(
                    id=uuid.uuid4().hex,
                    contract_id=contract_id,
                    trip_date=trip_date,
                    start_time=start_time,
                    end_time=end_time,
                    start_location=from_loc.strip(),
                    end_location=to_loc.strip(),
                    distance=distance,
                    duration=duration,
                    required_driver_class=class_s.strip(),
                )
                trips.append(trip)

    if not trips:
        raise ValueError("No trip rows found in PDF")

    return trips
