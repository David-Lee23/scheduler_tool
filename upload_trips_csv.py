# upload_trips_csv.py

import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)
# If using Transaction Pooler or Session Pooler, we want to ensure we disable SQLAlchemy client side pooling -
# https://docs.sqlalchemy.org/en/20/core/pooling.html#switching-pool-implementations
# engine = create_engine(DATABASE_URL, poolclass=NullPool)

# Test the connection
try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

# Load the CSV
csv_path = "parsed_schedule_031L0.csv"

# Read CSV with error handling for malformed lines
try:
    df = pd.read_csv(csv_path, on_bad_lines='skip')
    print(f"Successfully loaded CSV with {len(df)} rows")
except pd.errors.ParserError as e:
    print(f"Parser error: {e}")
    # Try alternative approach with different parameters
    try:
        df = pd.read_csv(csv_path, sep=',', quotechar='"', on_bad_lines='skip', engine='python')
        print(f"Successfully loaded CSV with alternative method: {len(df)} rows")
    except Exception as e2:
        print(f"Failed to load CSV: {e2}")
        exit(1)

# Clean/convert data types as needed
print("Data types before conversion:")
print(df.dtypes)
print("\nFirst few rows:")
print(df.head())

# The CSV structure is: id,trip_id,stop_number,nass_code,facility,arrive_time,load_unload,depart_time,vehicle,freq,freq_days,eff_date,exp_date,trip_miles,trip_hrs,drive_time
# But the nass_code column should contain codes like "030", and facility should contain location names

# Convert numeric columns with error handling
print("Converting data types...")
df["trip_id"] = pd.to_numeric(df["trip_id"], errors='coerce')

# For stop_number, handle cases where it's a string like "030PM" - we'll keep only numeric parts
df["stop_number"] = df["stop_number"].astype(str).str.extract(r'(\d+)')[0]
df["stop_number"] = pd.to_numeric(df["stop_number"], errors='coerce')

# freq should be TEXT according to schema, keep as string
df["freq"] = df["freq"].astype(str).replace('nan', None)

df["freq_days"] = pd.to_numeric(df["freq_days"], errors='coerce')
# Since freq_days has NOT NULL constraint, set a default value for NULL values
df["freq_days"] = df["freq_days"].fillna(0.0)
df["trip_miles"] = pd.to_numeric(df["trip_miles"], errors='coerce')
df["trip_hrs"] = pd.to_numeric(df["trip_hrs"], errors='coerce')
df["drive_time"] = pd.to_numeric(df["drive_time"], errors='coerce')

# Fill NaN values with 0.0 for numeric columns that might have NOT NULL constraints
df["trip_miles"] = df["trip_miles"].fillna(0.0)
df["trip_hrs"] = df["trip_hrs"].fillna(0.0)
df["drive_time"] = df["drive_time"].fillna(0.0)

# Handle date columns - they should be strings in format MM/DD/YYYY, convert them to proper dates
def clean_date(date_val):
    if pd.isna(date_val) or date_val == '' or str(date_val).lower() == 'nan':
        return None
    try:
        if isinstance(date_val, str) and '/' in date_val:
            # Convert MM/DD/YYYY to YYYY-MM-DD
            return pd.to_datetime(date_val, format='%m/%d/%Y').strftime('%Y-%m-%d')
        else:
            return None
    except:
        return None

df["eff_date"] = df["eff_date"].apply(clean_date)
df["exp_date"] = df["exp_date"].apply(clean_date)

# Since exp_date has NOT NULL constraint, set a default value for NULL dates
# Use a far future date for missing exp_date values
default_exp_date = '2099-12-31'
df["exp_date"] = df["exp_date"].fillna(default_exp_date)

# Handle eff_date as well in case it has NOT NULL constraint
default_eff_date = '2024-01-01'
df["eff_date"] = df["eff_date"].fillna(default_eff_date)

# Clean string columns - handle NaN and empty values
string_columns = ["nass_code", "facility", "arrive_time", "load_unload", "depart_time", "vehicle"]
for col in string_columns:
    df[col] = df[col].replace(['NaN', 'nan', ''], None)
    df[col] = df[col].where(pd.notnull(df[col]), None)

# Handle NOT NULL constraints for text fields by providing default values
df["nass_code"] = df["nass_code"].fillna("000")  # Default NASS code
df["facility"] = df["facility"].fillna("UNKNOWN")  # Default facility name
df["arrive_time"] = df["arrive_time"].fillna("00:00:00 ET")  # Default arrive time
df["load_unload"] = df["load_unload"].fillna("0 min")  # Default load/unload time
df["depart_time"] = df["depart_time"].fillna("00:00:00 ET")  # Default depart time
df["vehicle"] = df["vehicle"].fillna("UNK")  # Default vehicle code

# Report any rows with conversion issues
print(f"\nRows with NaN values after conversion:")
print(f"trip_id: {df['trip_id'].isna().sum()}")
print(f"stop_number: {df['stop_number'].isna().sum()}")

# Remove rows with invalid trip_id or stop_number since these are essential
initial_count = len(df)
df = df.dropna(subset=['trip_id', 'stop_number'])
final_count = len(df)
if initial_count != final_count:
    print(f"Removed {initial_count - final_count} rows with invalid trip_id or stop_number")

# Convert remaining NaN values to None for database compatibility  
import numpy as np
df = df.replace([np.nan, 'nan', 'NaN'], None)

print(f"\nFinal data shape: {df.shape}")
print("Sample of cleaned data:")
sample_data = df.head(2).to_dict('records')
for i, record in enumerate(sample_data):
    print(f"Record {i+1}:")
    for key, value in record.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    print()

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Reflect existing trips table
metadata = MetaData()
metadata.reflect(bind=engine)
trips_table = metadata.tables["trips"]

# Print the database schema to understand the expected data types
print("Database schema for trips table:")
for column in trips_table.columns:
    print(f"  {column.name}: {column.type}")

# Check if table already has data
from sqlalchemy import text
with engine.begin() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM trips"))
    existing_count = result.fetchone()[0]
    print(f"\nExisting records in trips table: {existing_count}")
    
    if existing_count > 0:
        print("Table already contains data. Options:")
        print("1. Clear existing data and insert new data")
        print("2. Skip id column and let database auto-generate ids")
        
        # For this script, we'll clear existing data to avoid conflicts
        print("Clearing existing data...")
        conn.execute(text("DELETE FROM trips"))
        print("Existing data cleared.")

# Upload each row
# Drop the id column to avoid duplicates and let the database auto-generate
df_without_id = df.drop(columns=['id'])

with engine.begin() as conn:
    conn.execute(trips_table.insert(), df_without_id.to_dict(orient="records"))

print(f"✅ Uploaded {len(df)} trip stops to Supabase!")

