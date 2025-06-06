# Scheduler Tool

This is a small Flask application for viewing schedule data uploaded from CSV files. A lightweight React frontend is served by Flask to browse contracts and trips stored in a SQLite database.

## Usage

1. **Load Data** (optional)

   If you have new CSV files, place them in the `csvs/` directory and run:

   ```bash
   python scheduale_uploader.py
   ```

   This will populate `scheduler.db` with the schedule information.

2. **Run the Server**

   ```bash
   python app.py
   ```

   The application will start a local Flask server on `http://localhost:5000`.
   Open that URL in a browser to access the React interface.

The interface lets you select a contract and trip and view detailed stop information.
