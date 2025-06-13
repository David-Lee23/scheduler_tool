#!/usr/bin/env python3
"""
MVP Trucking Schedule Management System
Simple PDF upload and trip management
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
import logging
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'trucking_schedule_mvp_2024'
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
DATABASE_PATH = 'trucking_schedule.db'

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

class SimpleDB:
    """Simple database operations"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query, params=(), fetch_one=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                return [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
                return cursor.lastrowid
    
    def ensure_shifts_table(self):
        """Create shifts table if it doesn't exist"""
        try:
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shift_name TEXT NOT NULL,
                    trip_ids TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    trip_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            logger.error(f"Error creating shifts table: {e}")

# Initialize database
db = SimpleDB()

# =============================================================================
# ROUTES - Main Pages
# =============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    try:
        total_trips = db.execute_query("SELECT COUNT(DISTINCT trip_id) as count FROM schedule")[0]['count']
    except:
        total_trips = 0
    return render_template('dashboard.html', total_trips=total_trips)

@app.route('/upload')
def upload_page():
    """PDF upload page"""
    return render_template('upload.html')

@app.route('/trips')
def trips_page():
    """Trip management page"""
    return render_template('trips.html')

@app.route('/shifts')
def shifts_page():
    """Shifts management page"""
    return render_template('shifts.html')

# =============================================================================
# API ROUTES - PDF Upload
# =============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Upload and process PDF file"""
    try:
        logger.info(f"Upload request received. Files: {list(request.files.keys())}")
        
        # Check for file in request
        if 'file' not in request.files:
            logger.error("No 'file' in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"File saved: {filepath}")
        
        # Process PDF to CSV
        csv_filepath = os.path.join(UPLOAD_FOLDER, f"{timestamp}_extracted.csv")
        
        try:
            # Run PDF extractor
            cmd = ['python', 'trucking_schedule_extractor.py', filepath, '-o', csv_filepath]
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            logger.info(f"Extractor output: {result.stdout}")
            if result.stderr:
                logger.error(f"Extractor errors: {result.stderr}")
            
            if result.returncode != 0:
                return jsonify({'error': f'PDF extraction failed: {result.stderr}'}), 500
            
            # Import CSV to database
            cmd = ['python', 'csv_to_sqlite.py', csv_filepath]
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            logger.info(f"Converter output: {result.stdout}")
            if result.stderr:
                logger.error(f"Converter errors: {result.stderr}")
            
            if result.returncode != 0:
                return jsonify({'error': f'Database import failed: {result.stderr}'}), 500
            
            # Count records
            try:
                record_count = db.execute_query("SELECT COUNT(*) as count FROM schedule")[0]['count']
            except:
                record_count = 0
            
            # Cleanup
            if os.path.exists(csv_filepath):
                os.remove(csv_filepath)
            
            logger.info(f"Successfully processed {filename}, {record_count} records")
            
            return jsonify({
                'message': 'PDF processed successfully',
                'filename': filename,
                'records': record_count
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'Processing timed out'}), 500
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ROUTES - Trip Management
# =============================================================================

@app.route('/api/trips')
def get_trips():
    """Get all trips with essential info for shift building"""
    try:
        trips = db.execute_query("""
            SELECT 
                trip_id,
                MIN(arrive_time) as start_time,
                MAX(depart_time) as end_time,
                MIN(facility) as start_location,
                MAX(facility) as end_location,
                COUNT(*) as stop_count,
                vehicle_type,
                vehicle_id
            FROM schedule 
            GROUP BY trip_id
            ORDER BY trip_id
        """)
        
        return jsonify({'trips': trips})
        
    except Exception as e:
        logger.error(f"Get trips error: {e}")
        return jsonify({'trips': []})

@app.route('/api/trips/<int:trip_id>')
def get_trip_details(trip_id):
    """Get detailed trip information"""
    try:
        stops = db.execute_query("""
            SELECT * FROM schedule 
            WHERE trip_id = ? 
            ORDER BY stop_number
        """, (trip_id,))
        
        if not stops:
            return jsonify({'error': 'Trip not found'}), 404
        
        return jsonify({'trip_id': trip_id, 'stops': stops})
        
    except Exception as e:
        logger.error(f"Get trip details error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/shifts', methods=['GET'])
def get_shifts():
    """Get all created shifts"""
    try:
        db.ensure_shifts_table()
        shifts = db.execute_query("""
            SELECT id, shift_name, trip_ids, start_time, end_time, 
                   trip_count, created_at 
            FROM shifts 
            ORDER BY created_at DESC
        """)
        
        # Parse trip_ids back to arrays
        for shift in shifts:
            shift['trip_ids'] = [int(x) for x in shift['trip_ids'].split(',')]
        
        return jsonify({'shifts': shifts})
        
    except Exception as e:
        logger.error(f"Get shifts error: {e}")
        return jsonify({'shifts': []})

@app.route('/api/shifts', methods=['POST'])
def create_shift():
    """Create a shift from selected trips"""
    try:
        db.ensure_shifts_table()
        
        data = request.get_json()
        trip_ids = data.get('trip_ids', [])
        shift_name = data.get('shift_name', f"Shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not trip_ids:
            return jsonify({'error': 'No trips selected'}), 400
        
        # Get trip details
        placeholders = ','.join(['?' for _ in trip_ids])
        trips = db.execute_query(f"""
            SELECT trip_id, MIN(arrive_time) as start_time, MAX(depart_time) as end_time
            FROM schedule 
            WHERE trip_id IN ({placeholders})
            GROUP BY trip_id
        """, trip_ids)
        
        if trips:
            earliest_start = min(trip['start_time'] for trip in trips)
            latest_end = max(trip['end_time'] for trip in trips)
            
            # Store shift in database
            shift_id = db.execute_query("""
                INSERT INTO shifts (shift_name, trip_ids, start_time, end_time, trip_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                shift_name,
                ','.join(map(str, trip_ids)),
                earliest_start,
                latest_end,
                len(trip_ids)
            ))
            
            return jsonify({
                'message': 'Shift created successfully',
                'shift': {
                    'id': shift_id,
                    'shift_name': shift_name,
                    'trip_ids': trip_ids,
                    'start_time': earliest_start,
                    'end_time': latest_end,
                    'trip_count': len(trip_ids)
                }
            })
        
        return jsonify({'error': 'No valid trips found'}), 400
        
    except Exception as e:
        logger.error(f"Create shift error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/shifts/<int:shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    """Delete a shift"""
    try:
        db.execute_query("DELETE FROM shifts WHERE id = ?", (shift_id,))
        return jsonify({'message': 'Shift deleted successfully'})
    except Exception as e:
        logger.error(f"Delete shift error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 