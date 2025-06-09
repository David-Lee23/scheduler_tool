import os
from supabase import create_client, Client
from typing import List
from models.trip import Trip

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError('Supabase credentials not set.')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_trips_to_supabase(trips: List[Trip]):
    client = _get_client()
    client.table('trips').insert([trip.__dict__ for trip in trips]).execute()
