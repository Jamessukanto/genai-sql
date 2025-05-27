PARTITIONED_TABLES = ["raw_telemetry", "processed_metrics"]

# Order of table creation matters due to foreign key constraints
CREATE_TABLE_QUERIES = {
    "fleets": """
        CREATE TABLE IF NOT EXISTS fleets (
            fleet_id TEXT PRIMARY KEY,
            name TEXT,
            country TEXT,
            time_zone TEXT
    );""",
    "drivers": """
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id TEXT PRIMARY KEY,
            fleet_id TEXT REFERENCES fleets(fleet_id),
            name TEXT,
            license_no TEXT,
            hire_date DATE
    );""",
    "vehicles": """
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id TEXT PRIMARY KEY,
            vin TEXT UNIQUE,
            fleet_id TEXT REFERENCES fleets(fleet_id),
            model TEXT,
            make TEXT,
            variant TEXT,
            registration_no TEXT,
            purchase_date DATE
    );""",
    "alerts": """
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            vehicle_id TEXT REFERENCES vehicles(vehicle_id),
            alert_type TEXT,
            severity TEXT,
            alert_ts TIMESTAMP,
            value DOUBLE PRECISION,
            threshold DOUBLE PRECISION,
            resolved_bool BOOLEAN,
            resolved_ts TIMESTAMP
    );""",
    "geofence_events": """
        CREATE TABLE IF NOT EXISTS geofence_events (
            event_id TEXT PRIMARY KEY,
            vehicle_id TEXT REFERENCES vehicles(vehicle_id),
            geofence_name TEXT,
            enter_ts TIMESTAMP,
            exit_ts TIMESTAMP
    );""",
    "maintenance_logs": """
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            maint_id TEXT PRIMARY KEY,
            vehicle_id TEXT REFERENCES vehicles(vehicle_id),
            maint_type TEXT,
            start_ts TIMESTAMP,
            end_ts TIMESTAMP,
            cost_sgd DOUBLE PRECISION,
            notes TEXT
    );""",
    "battery_cycles": """
        CREATE TABLE IF NOT EXISTS battery_cycles (
            cycle_id TEXT PRIMARY KEY,
            vehicle_id TEXT REFERENCES vehicles(vehicle_id),
            ts TIMESTAMP,
            dod_pct DOUBLE PRECISION,
            soh_pct DOUBLE PRECISION
    );""",
    # Note the partitioning by vehicle_id
    "raw_telemetry": """
        CREATE TABLE IF NOT EXISTS raw_telemetry (
            ts TIMESTAMP NOT NULL,
            vehicle_id TEXT NOT NULL,
            soc_pct DOUBLE PRECISION,
            pack_voltage_v DOUBLE PRECISION,
            pack_current_a DOUBLE PRECISION,
            batt_temp_c DOUBLE PRECISION,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            speed_kph DOUBLE PRECISION,
            odo_km DOUBLE PRECISION
        ) PARTITION BY LIST (vehicle_id);
    """,
    # Note the partitioning by vehicle_id
    "processed_metrics": """
        CREATE TABLE IF NOT EXISTS processed_metrics (
            ts TIMESTAMP NOT NULL,
            vehicle_id TEXT NOT NULL,
            avg_speed_kph_15m DOUBLE PRECISION,
            distance_km_15m DOUBLE PRECISION,
            energy_kwh_15m DOUBLE PRECISION,
            battery_health_pct DOUBLE PRECISION,
            soc_band TEXT
        ) PARTITION BY LIST (vehicle_id);
    """,
    "charging_sessions": """
        CREATE TABLE IF NOT EXISTS charging_sessions (
            session_id TEXT PRIMARY KEY,
            vehicle_id TEXT REFERENCES vehicles(vehicle_id),
            start_ts TIMESTAMP,
            end_ts TIMESTAMP,
            start_soc DOUBLE PRECISION,
            end_soc DOUBLE PRECISION,
            energy_kwh DOUBLE PRECISION,
            location TEXT
    );""",
    "trips": """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY,
            vehicle_id TEXT REFERENCES vehicles(vehicle_id),
            start_ts TIMESTAMP,
            end_ts TIMESTAMP,
            distance_km DOUBLE PRECISION,
            energy_kwh DOUBLE PRECISION,
            idle_minutes DOUBLE PRECISION,
            avg_temp_c DOUBLE PRECISION
    );""",
    "driver_trip_map": """
        CREATE TABLE IF NOT EXISTS driver_trip_map (
            trip_id TEXT REFERENCES trips(trip_id),
            driver_id TEXT REFERENCES drivers(driver_id),
            primary_bool BOOLEAN DEFAULT TRUE
    );""",
    "fleet_daily_summary": """
        CREATE TABLE IF NOT EXISTS fleet_daily_summary (
            fleet_id TEXT REFERENCES fleets(fleet_id),
            date DATE,
            total_distance_km DOUBLE PRECISION,
            total_energy_kwh DOUBLE PRECISION,
            active_vehicles INTEGER,
            avg_soc_pct DOUBLE PRECISION
);"""
}


