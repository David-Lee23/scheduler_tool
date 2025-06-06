from optimizer import Stop, generate_shifts


def test_generate_shifts_basic():
    stops = [
        Stop("A", 3),
        Stop("B", 4),
        Stop("C", 3),
        Stop("D", 2),  # total 12 hours
        Stop("E", 3),
        Stop("F", 7),  # total 10 hours
    ]

    shifts = generate_shifts(stops)
    assert len(shifts) == 2

    for shift in shifts:
        assert 10 <= shift.total_hours <= 12
        facilities = [s.facility for s in shift.stops]
        # ensure no backtracking within a shift
        assert facilities == sorted(facilities, key=facilities.index)

    assert [s.facility for s in shifts[0].stops] == ["A", "B", "C", "D"]
    assert [s.facility for s in shifts[1].stops] == ["E", "F"]
