import argparse
from parsers.parse_pdf import parse_pdf
from db.supabase_client import upload_trips_to_supabase, load_drivers_from_supabase, store_shifts_to_supabase
from optimizer.schedule_optimizer import run_optimizer

parser = argparse.ArgumentParser(description='Shift optimizer pipeline')
parser.add_argument('pdf_path', help='Path to contract PDF')
args = parser.parse_args()

trips = parse_pdf(args.pdf_path)
upload_trips_to_supabase(trips)

drivers = load_drivers_from_supabase()
shifts = run_optimizer(trips, drivers)
store_shifts_to_supabase(shifts)

print('[main] Done.')
