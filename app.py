from pathlib import Path
from flask import Flask, jsonify, abort, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{Path(__file__).with_name('scheduler.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    contract_id = db.Column(db.String, primary_key=True)
    trip_id = db.Column(db.Integer, primary_key=True)
    stop_number = db.Column(db.Integer, primary_key=True)
    nass_code = db.Column(db.String, nullable=False)
    facility = db.Column(db.String, nullable=False)
    arrive_time = db.Column(db.String, nullable=False)
    load_unload = db.Column(db.String, nullable=False)
    depart_time = db.Column(db.String, nullable=False)
    vehicle_frequency = db.Column(db.String, nullable=False)
    freq_days = db.Column(db.String, nullable=False)
    eff_date = db.Column(db.String, nullable=False)
    exp_date = db.Column(db.String, nullable=False)
    trip_miles = db.Column(db.Float, nullable=False)
    trip_hours = db.Column(db.Float, nullable=False)
    drive_time = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    """Serve the React front-end."""
    return render_template('index.html')

@app.route('/contracts')
def get_contracts():
    contracts = db.session.query(Schedule.contract_id).distinct().all()
    return jsonify([c[0] for c in contracts])

@app.route('/contracts/<contract_id>/trips')
def get_trips(contract_id):
    trips = db.session.query(Schedule.trip_id).\
        filter(Schedule.contract_id == contract_id).distinct().all()
    if not trips:
        abort(404)
    return jsonify([t[0] for t in trips])

@app.route('/contracts/<contract_id>/trips/<int:trip_id>')
def get_trip_details(contract_id, trip_id):
    stops = Schedule.query.filter_by(contract_id=contract_id, trip_id=trip_id).\
        order_by(Schedule.stop_number).all()
    if not stops:
        abort(404)
    result = [
        {
            'stop_number': s.stop_number,
            'nass_code': s.nass_code,
            'facility': s.facility,
            'arrive_time': s.arrive_time,
            'load_unload': s.load_unload,
            'depart_time': s.depart_time,
            'vehicle_frequency': s.vehicle_frequency,
            'freq_days': s.freq_days,
            'eff_date': s.eff_date,
            'exp_date': s.exp_date,
            'trip_miles': s.trip_miles,
            'trip_hours': s.trip_hours,
            'drive_time': s.drive_time,
        }
        for s in stops
    ]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
