function ScheduleApp() {
  const [contracts, setContracts] = React.useState([]);
  const [selectedContract, setSelectedContract] = React.useState('');
  const [trips, setTrips] = React.useState([]);
  const [selectedTrip, setSelectedTrip] = React.useState('');
  const [tripDetails, setTripDetails] = React.useState([]);
  const [selectedDate, setSelectedDate] = React.useState('');
  const [shifts, setShifts] = React.useState([]);

  React.useEffect(() => {
    fetch('/contracts')
      .then(res => res.json())
      .then(data => setContracts(data))
      .catch(console.error);
  }, []);

  React.useEffect(() => {
    if (selectedContract) {
      fetch(`/contracts/${selectedContract}/trips`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch trips');
          return res.json();
        })
        .then(setTrips)
        .catch(() => setTrips([]));
    } else {
      setTrips([]);
    }
    setSelectedTrip('');
  }, [selectedContract]);

  React.useEffect(() => {
    if (selectedContract && selectedTrip) {
      fetch(`/contracts/${selectedContract}/trips/${selectedTrip}`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch details');
          return res.json();
        })
        .then(setTripDetails)
        .catch(() => setTripDetails([]));
    } else {
      setTripDetails([]);
    }
  }, [selectedContract, selectedTrip]);

  React.useEffect(() => {
    if (selectedDate) {
      fetch(`/optimized-shifts/${selectedDate}`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch shifts');
          return res.json();
        })
        .then(setShifts)
        .catch(() => setShifts([]));
    } else {
      setShifts([]);
    }
  }, [selectedDate]);

  return (
    <div>
      <h1>Schedule Viewer</h1>
      <div>
        <label>
          Contract:
          <select value={selectedContract} onChange={e => setSelectedContract(e.target.value)}>
            <option value="">Select Contract</option>
            {contracts.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        {trips.length > 0 && (
          <label>
            Trip:
            <select value={selectedTrip} onChange={e => setSelectedTrip(e.target.value)}>
              <option value="">Select Trip</option>
              {trips.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>
        )}
      </div>

      {tripDetails.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Stop</th>
              <th>NASS Code</th>
              <th>Facility</th>
              <th>Arrive</th>
              <th>Load/Unload</th>
              <th>Depart</th>
              <th>Frequency</th>
              <th>Days</th>
              <th>Eff Date</th>
              <th>Exp Date</th>
              <th>Miles</th>
              <th>Hours</th>
              <th>Drive Time</th>
            </tr>
          </thead>
          <tbody>
            {tripDetails.map((stop, idx) => (
              <tr key={idx}>
                <td>{stop.stop_number}</td>
                <td>{stop.nass_code}</td>
                <td>{stop.facility}</td>
                <td>{stop.arrive_time}</td>
                <td>{stop.load_unload}</td>
                <td>{stop.depart_time}</td>
                <td>{stop.vehicle_frequency}</td>
                <td>{stop.freq_days}</td>
                <td>{stop.eff_date}</td>
                <td>{stop.exp_date}</td>
                <td>{stop.trip_miles}</td>
                <td>{stop.trip_hours}</td>
                <td>{stop.drive_time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <hr />
      <h2>Optimized Shifts</h2>
      <label>
        Date:
        <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} />
      </label>

      {shifts.map((shift, sIdx) => (
        <div key={shift.id || shift.shift_id || sIdx} style={{ marginTop: '20px' }}>
          <h3>{shift.shift_id || shift.id || `Shift ${sIdx + 1}`}</h3>
          {Array.isArray(shift.stops) && shift.stops.length > 0 && (() => {
            const cols = Object.keys(shift.stops[0]);
            return (
              <table>
                <thead>
                  <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
                </thead>
                <tbody>
                  {shift.stops.map((stop, idx) => (
                    <tr key={idx}>{cols.map(c => <td key={c}>{stop[c]}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            );
          })()}
        </div>
      ))}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<ScheduleApp />);
