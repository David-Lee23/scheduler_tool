import argparse
from parsers.parse_pdf import parse_pdf
from db.supabase_client import upload_trips_to_supabase

parser = argparse.ArgumentParser(description='Trip uploader pipeline')
parser.add_argument('pdf_path', help='Path to contract PDF')
args = parser.parse_args()

trips = parse_pdf(args.pdf_path)
upload_trips_to_supabase(trips)

print('[main] Done. Trips uploaded.')
