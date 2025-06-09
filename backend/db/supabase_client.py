"""Simple Supabase client wrapper."""
import os
from supabase import create_client, Client
from typing import List
from models.trip import Trip
from models.shift import DriverShift
import json

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError('Supabase credentials not set.')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_trips_to_supabase(trips: List[Trip]):
    client = _get_client()
    client.table('trips').insert([trip.__dict__ for trip in trips]).execute()

def load_drivers_from_supabase():
    client = _get_client()
    data = client.table('drivers').select('*').execute().data
    # Build Driver objects (left as exercise)
    return data

def store_shifts_to_supabase(shifts: List[DriverShift]):
    client = _get_client()
    # Insert shifts and shift-trip mappings (left as exercise)
    for shift in shifts:
        client.table('driver_shifts').insert({
            'id': shift.id,
            'driver_id': shift.driver_id,
            'shift_date': shift.shift_date.isoformat(),
            'total_hours': shift.total_hours,
            'total_miles': shift.total_miles,
        }).execute()
