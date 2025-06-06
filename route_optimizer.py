from datetime import datetime, date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, Date, create_engine

from scheduale_uploader import Base, Schedules


class OptimizedShift(Base):
    __tablename__ = "optimized_shifts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    shift_id = Column(Integer, nullable=False)
    stop_sequence = Column(String, nullable=False)
    total_miles = Column(Float, nullable=False)
    total_hours = Column(Float, nullable=False)


def _parse_date(text: str) -> date:
    """Parse a MM/DD/YYYY string to a date. Return today() if parsing fails."""
    try:
        return datetime.strptime(text.split()[0], "%m/%d/%Y").date()
    except Exception:
        return date.today()


def populate_optimized_shifts(db_url: str = "sqlite:///scheduler.db") -> None:
    """Create optimized shifts based on schedule data."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing optimized shifts
    session.query(OptimizedShift).delete()

    # Query distinct trips ordered by contract then trip id
    trips = (
        session.query(
            Schedules.contract_id,
            Schedules.trip_id,
            Schedules.eff_date,
            Schedules.trip_miles,
            Schedules.trip_hours,
        )
        .group_by(Schedules.contract_id, Schedules.trip_id)
        .order_by(Schedules.contract_id, Schedules.trip_id)
        .all()
    )

    current_contract = None
    shift_id = 1
    current_hours = 0.0
    current_miles = 0.0
    current_stops: list[str] = []
    current_date = date.today()

    def finalize_shift():
        nonlocal shift_id, current_hours, current_miles, current_stops
        if not current_stops:
            return
        shift = OptimizedShift(
            contract_id=current_contract,
            date=current_date,
            shift_id=shift_id,
            stop_sequence=",".join(current_stops),
            total_miles=current_miles,
            total_hours=current_hours,
        )
        session.add(shift)
        shift_id += 1
        current_hours = 0.0
        current_miles = 0.0
        current_stops = []

    for trip in trips:
        if current_contract != trip.contract_id:
            finalize_shift()
            session.flush()
            current_contract = trip.contract_id
            shift_id = 1
            current_hours = 0.0
            current_miles = 0.0
            current_stops = []
            current_date = _parse_date(trip.eff_date)

        # gather stop ids
        stops = (
            session.query(Schedules)
            .filter_by(contract_id=trip.contract_id, trip_id=trip.trip_id)
            .order_by(Schedules.stop_number)
            .all()
        )
        stop_ids = [f"{s.contract_id}:{s.trip_id}:{s.stop_number}" for s in stops]
        trip_hours = trip.trip_hours or 0.0
        trip_miles = trip.trip_miles or 0.0

        if current_hours + trip_hours > 12 and current_hours >= 10:
            finalize_shift()
            current_date = _parse_date(trip.eff_date)

        current_stops.extend(stop_ids)
        current_hours += trip_hours
        current_miles += trip_miles

    finalize_shift()
    session.commit()
    session.close()


if __name__ == "__main__":
    populate_optimized_shifts()

