import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY
const supabase = createClient(supabaseUrl, supabaseKey)

function App() {
  const [trips, setTrips] = useState([])

  useEffect(() => {
    supabase.from('trips').select('*').then(({ data, error }) => {
      if (error) console.error(error)
      else setTrips(data)
    })
  }, [])

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Trips</h1>
      <ul className="list-disc pl-5">
        {trips.map(trip => (
          <li key={trip.id}>
            {trip.contract_id} - {trip.start_location} ➡️ {trip.end_location} ({trip.trip_date})
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App
