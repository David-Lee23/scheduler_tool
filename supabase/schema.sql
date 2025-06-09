-- Supabase schema for Trip Manager
create extension if not exists "pgcrypto";

create table if not exists trips (
    id uuid primary key default gen_random_uuid(),
    contract_id text not null,
    trip_date date not null,
    start_time time not null,
    end_time time not null,
    start_location text,
    end_location text,
    distance numeric,
    duration numeric,
    required_driver_class text
);
