import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import scheduale_uploader as su


def test_parse_simple_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "sample.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "1", "1", "AAA", "FAC1", "01:00", "10", "01:10", "X", "", "Mon", "2025-01-01 2025-12-31",
        ])
        writer.writerow(["1", "2", "BBB", "FAC2", "02:00", "10", "02:10", "", "", "", ""])
        writer.writerow(["", "", "100", "11", "", "", "5"])

    db_path = tmp_path / "test.db"

    def fake_engine(url):
        return create_engine(f"sqlite:///{db_path}")

    monkeypatch.setattr(su, "create_engine", fake_engine)

    su.process_schedules(tmp_path)

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    rows = session.query(su.Schedules).order_by(su.Schedules.stop_number).all()
    assert len(rows) == 2
    assert rows[0].nass_code == "AAA"
    assert rows[0].vehicle_frequency == "X"
    assert rows[1].facility == "FAC2"
    assert rows[0].trip_miles == 100.0
    assert rows[0].trip_hours == 11.0
    assert rows[0].drive_time == 5.0
