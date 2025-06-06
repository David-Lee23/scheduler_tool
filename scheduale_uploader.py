# scheduale_uploader.py
# Use ZAMZAR.com to convert pdfs to csvs.

import os
from pathlib import Path
import re
from datetime import datetime
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Date, Float, PrimaryKeyConstraint
from sqlalchemy import create_engine
import csv

folder_path = Path(__file__).parent / "csvs"
csv_files = list(folder_path.glob("*.csv"))

class Base(DeclarativeBase):
    pass

class Schedules(Base):
    __tablename__ = "schedules"

    contract_id = Column(String, nullable=False)
    trip_id = Column(Integer, nullable=False)
    stop_number = Column(Integer, nullable=False)
    nass_code = Column(String, nullable=False)
    facility = Column(String, nullable=False)
    arrive_time = Column(String, nullable=False)
    load_unload = Column(String, nullable=False)
    depart_time = Column(String, nullable=False)
    vehicle_frequency = Column(String, nullable=False)
    freq_days = Column(String, nullable=False)
    eff_date = Column(String, nullable=False)
    exp_date = Column(String, nullable=False)
    trip_miles = Column(Float, nullable=False)
    trip_hours = Column(Float, nullable=False)
    drive_time = Column(Float, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("contract_id", "trip_id", "stop_number"),
    )

def clean_number(value):
    """
    Cleans a string to produce a float number.
    Returns 0.0 if conversion is not possible, as database columns are non-nullable.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(',', '').replace('?', '').strip())
    except (ValueError, TypeError):
        # Mute the error message to prevent clutter for expected non-numeric values
        # print(f"Could not convert to number: {value}. Using 0.0 as default.")
        return 0.0

def process_schedules(folder_path):
    """
    Processes complex, non-flat CSV files by reading line-by-line,
    buffering stops, and applying trip-summary data retrospectively.
    """
    engine = create_engine('sqlite:///scheduler.db')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for file_path in csv_files:
        print(f"📄 Processing {file_path.name}")
        contract_id = file_path.stem.split()[1][:5]

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            current_trip_stops = []
            trip_level_data = {}

            for row in reader:
                # Skip empty rows
                if not any(field.strip() for field in row):
                    continue

                # Skip header-like rows
                row_start = row[0].strip()
                if row_start.startswith("HCR#") or row_start.startswith("Trip"):
                    continue

                # Check if it's a trip summary data row.
                # These rows have empty first two columns and a number in the third.
                if row[0].strip() == "" and row[1].strip() == "" and clean_number(row[2]) > 0:
                    trip_miles = clean_number(row[2])
                    trip_hours = clean_number(row[3])
                    # Drive time is sometimes in the 7th column (index 6)
                    drive_time = clean_number(row[6])

                    if not current_trip_stops:
                        continue

                    # Apply summary data to all buffered stops for the trip
                    for stop in current_trip_stops:
                        stop.trip_miles = trip_miles
                        stop.trip_hours = trip_hours
                        stop.drive_time = drive_time
                        session.merge(stop)

                    try:
                        session.commit()
                        trip_id_for_print = current_trip_stops[0].trip_id
                        print(f"  -> Committed Trip ID {trip_id_for_print} with {len(current_trip_stops)} stops.")
                    except Exception as e:
                        print(f"  -> ERROR committing Trip ID {current_trip_stops[0].trip_id}: {e}")
                        session.rollback()

                    # Clear buffer and reset trip data for the next trip
                    current_trip_stops = []
                    trip_level_data = {}
                    continue

                # Try to process the row as a standard stop row
                try:
                    trip_id = int(row[0])
                    stop_number = int(row[1])
                except (ValueError, IndexError):
                    # Not a valid stop row, so skip
                    continue

                # If it's the first stop, capture trip-level data that will be
                # applied to all subsequent stops of this trip.
                if stop_number == 1:
                    trip_level_data['vehicle_frequency'] = row[7].strip()
                    trip_level_data['freq_days'] = row[9].strip()
                    # Dates are combined in the 11th column (index 10)
                    if len(row) > 10:
                        dates = row[10].split()
                        trip_level_data['eff_date'] = dates[0] if len(dates) > 0 else ""
                        trip_level_data['exp_date'] = dates[1] if len(dates) > 1 else ""
                    else:
                        trip_level_data['eff_date'] = ""
                        trip_level_data['exp_date'] = ""


                # Create the Schedules object for the current stop
                v = Schedules(
                    contract_id=contract_id,
                    trip_id=trip_id,
                    stop_number=stop_number,
                    nass_code=row[2].strip(),
                    facility=row[3].strip(),
                    arrive_time=row[4].strip(),
                    load_unload=row[5].strip(),
                    depart_time=row[6].strip(),
                    # Use carried-forward data from the first stop
                    vehicle_frequency=trip_level_data.get('vehicle_frequency', ""),
                    freq_days=trip_level_data.get('freq_days', ""),
                    eff_date=trip_level_data.get('eff_date', ""),
                    exp_date=trip_level_data.get('exp_date', ""),
                    # Trip summary data is added later as a placeholder
                    trip_miles=0.0,
                    trip_hours=0.0,
                    drive_time=0.0
                )
                current_trip_stops.append(v)

        print(f"✅ Finished processing {file_path.name}")

if __name__ == "__main__":
    folder_path = Path(__file__).parent / "csvs"
    # Create the folder if it doesn't exist
    folder_path.mkdir(exist_ok=True) 
    print(f"Looking for CSV files in: {folder_path.resolve()}")
    process_schedules(folder_path)
    print("Database upload process complete.")