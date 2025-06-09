-- Supabase schema for Shift Optimizer
create extension if not exists "pgcrypto";

create table if not exists drivers (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    driver_class text not null,
    max_hours_per_day int not null,
    home_base text
);

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

create table if not exists driver_shifts (
    id uuid primary key default gen_random_uuid(),
    driver_id uuid references drivers(id),
    shift_date date not null,
    total_hours numeric,
    total_miles numeric
);

create table if not exists driver_shift_trips (
    shift_id uuid references driver_shifts(id),
    trip_id uuid references trips(id),
    trip_order int,
    primary key (shift_id, trip_id)
);
