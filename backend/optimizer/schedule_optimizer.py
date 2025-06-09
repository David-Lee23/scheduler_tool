"""Simple OR-Tools example optimizer.

Replace the objective and constraints with your real business rules.
"""
from ortools.sat.python import cp_model
from typing import List
from models.trip import Trip
from models.driver import Driver
from models.shift import DriverShift
import uuid
import datetime as dt

def run_optimizer(trips: List[Trip], drivers: List[Driver]) -> List[DriverShift]:
    model = cp_model.CpModel()

    # Variables: X[d][t] = 1 if driver d takes trip t
    x = {}
    for d_idx, _ in enumerate(drivers):
        for t_idx, _ in enumerate(trips):
            x[(d_idx, t_idx)] = model.NewBoolVar(f'x_{d_idx}_{t_idx}')

    # Constraint: each trip must be assigned to exactly one driver
    for t_idx, _ in enumerate(trips):
        model.Add(sum(x[(d_idx, t_idx)] for d_idx in range(len(drivers))) == 1)

    # Constraint: driver max daily hours (very simplified)
    for d_idx, driver in enumerate(drivers):
        total_hours = sum(
            x[(d_idx, t_idx)] * trips[t_idx].duration
            for t_idx, _ in enumerate(trips)
        )
        model.Add(total_hours <= driver.max_hours_per_day)

    # Objective: minimize total hours (demo)
    model.Minimize(
        sum(
            x[(d_idx, t_idx)] * trips[t_idx].duration
            for d_idx in range(len(drivers))
            for t_idx in range(len(trips))
        )
    )

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.Solve(model)
    shifts = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for d_idx, driver in enumerate(drivers):
            assigned_trips = [trips[t_idx] for t_idx in range(len(trips)) if solver.Value(x[(d_idx, t_idx)]) == 1]
            if not assigned_trips:
                continue
            total_hours = sum(t.duration for t in assigned_trips)
            total_miles = sum(t.distance for t in assigned_trips)
            shifts.append(
                DriverShift(
                    id=str(uuid.uuid4()),
                    driver_id=driver.id,
                    shift_date=assigned_trips[0].trip_date,
                    trips=assigned_trips,
                    total_hours=total_hours,
                    total_miles=total_miles,
                )
            )
    else:
        print("[optimizer] No feasible solution found.")
    return shifts
