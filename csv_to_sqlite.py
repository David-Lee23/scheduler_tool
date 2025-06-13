#!/usr/bin/env python3
"""
Simple CSV to SQLite Database for MVP
Basic trucking schedule database for PDF upload and trip management
"""

import sqlite3
import pandas as pd
import re
from datetime import datetime, time
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleTruckingDB:
    def __init__(self, db_path='trucking_schedule.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Create database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_schema(self):
        """Create simplified database schema for MVP."""
        
        # Simple schedule table - flexible columns for any PDF format
        schedule_table_sql = """
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            stop_number INTEGER NOT NULL,
            nass_code TEXT,
            facility TEXT NOT NULL,
            arrive_time TEXT,
            depart_time TEXT,
            load_unload_duration TEXT,
            vehicle_type TEXT,
            vehicle_id TEXT,
            frequency TEXT,
            effective_date TEXT,
            expiration_date TEXT,
            raw_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Basic indexes for performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_trip_id ON schedule(trip_id);",
            "CREATE INDEX IF NOT EXISTS idx_facility ON schedule(facility);",
            "CREATE INDEX IF NOT EXISTS idx_arrive_time ON schedule(arrive_time);",
            "CREATE INDEX IF NOT EXISTS idx_vehicle_id ON schedule(vehicle_id);"
        ]
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(schedule_table_sql)
            
            for index_sql in indexes_sql:
                cursor.execute(index_sql)
            
            self.conn.commit()
            logger.info("Simple database schema created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise
    
    def load_csv_data(self, csv_file_path):
        """Load CSV data with flexible column handling."""
        try:
            logger.info(f"Reading CSV file: {csv_file_path}")
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded {len(df)} records from CSV")
            
            # Clean and prepare data
            records = []
            for _, row in df.iterrows():
                try:
                    record = (
                        int(row['trip_id']) if pd.notna(row['trip_id']) else None,
                        int(row['stop_number']) if pd.notna(row['stop_number']) else None,
                        str(row['nass_code']) if pd.notna(row['nass_code']) else None,
                        str(row['facility']) if pd.notna(row['facility']) else None,
                        str(row['arrive_time']) if pd.notna(row['arrive_time']) else None,
                        str(row['depart_time']) if pd.notna(row['depart_time']) else None,
                        str(row['load_unload_duration']) if pd.notna(row['load_unload_duration']) else None,
                        str(row['vehicle_type']) if pd.notna(row['vehicle_type']) else None,
                        str(row['vehicle_id']) if pd.notna(row['vehicle_id']) else None,
                        str(row['frequency']) if pd.notna(row['frequency']) else None,
                        str(row['effective_date']) if pd.notna(row['effective_date']) else None,
                        str(row['expiration_date']) if pd.notna(row['expiration_date']) else None,
                        str(row['raw_data']) if pd.notna(row['raw_data']) else None
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping row due to error: {e}")
                    continue
            
            # Insert records
            insert_sql = """
            INSERT OR REPLACE INTO schedule 
            (trip_id, stop_number, nass_code, facility, arrive_time, depart_time, 
             load_unload_duration, vehicle_type, vehicle_id, frequency, 
             effective_date, expiration_date, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor = self.conn.cursor()
            cursor.executemany(insert_sql, records)
            self.conn.commit()
            
            logger.info(f"Successfully inserted {len(records)} schedule records")
            return len(records)
            
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            raise
    
    def get_stats(self):
        """Get basic database statistics."""
        try:
            cursor = self.conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM schedule")
            total_records = cursor.fetchone()[0]
            
            # Unique trips
            cursor.execute("SELECT COUNT(DISTINCT trip_id) FROM schedule")
            unique_trips = cursor.fetchone()[0]
            
            # Unique facilities
            cursor.execute("SELECT COUNT(DISTINCT facility) FROM schedule")
            unique_facilities = cursor.fetchone()[0]
            
            return {
                'total_records': total_records,
                'unique_trips': unique_trips,
                'unique_facilities': unique_facilities
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total_records': 0, 'unique_trips': 0, 'unique_facilities': 0}
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """Main function to process CSV and create database."""
    
    # Get CSV file from command line argument
    if len(sys.argv) < 2:
        print("Usage: python csv_to_sqlite.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    db_file = 'trucking_schedule.db'
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        sys.exit(1)
    
    # Remove existing database to start fresh
    if os.path.exists(db_file):
        os.remove(db_file)
        logger.info(f"Removed existing database: {db_file}")
    
    # Create database
    db = SimpleTruckingDB(db_file)
    
    try:
        # Connect and setup
        db.connect()
        db.create_schema()
        
        # Load data
        logger.info("Starting data import...")
        record_count = db.load_csv_data(csv_file)
        
        # Get stats
        stats = db.get_stats()
        
        # Summary
        logger.info("="*60)
        logger.info("SIMPLE DATABASE CREATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Database file: {db_file}")
        logger.info(f"Records imported: {record_count}")
        logger.info(f"Unique trips: {stats['unique_trips']}")
        logger.info(f"Unique facilities: {stats['unique_facilities']}")
        logger.info(f"Database size: {os.path.getsize(db_file) / 1024:.2f} KB")
        logger.info("Simple database ready for MVP!")
        
    except Exception as e:
        logger.error(f"Database creation failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 