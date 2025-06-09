# Shift Optimizer Starter Repo

This repo is a starter template for building a **Shift Optimizer** web app.

## Architecture
- **Backend (Python)**: parse contract PDFs into trips, run OR-Tools optimization, and store results in Supabase.
- **Database**: Supabase Postgres (schema provided in `supabase/schema.sql`).
- **Frontend (React + Supabase JS)**: display trips and optimized shifts.

See the `/backend/README_backend.md` and `/frontend/README_frontend.md` for quick‑start instructions.
