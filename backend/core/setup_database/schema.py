from databases import Database
from sqlalchemy import text
from typing import Dict, List


# ============================================================================
# TABLE DEFINITIONS
# ============================================================================

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


# ============================================================================
# SCHEMA MANAGEMENT
# ============================================================================

async def enable_rls(database: Database, table: str) -> None:
    """Enable row-level security on a table with fleet_id-based isolation."""
    policy = f"fleet_isolation_{table}"

    try:
        await database.execute(text(f"DROP POLICY IF EXISTS {policy} ON {table};"))
        
        # Create policy
        policy_sql = f"""
        CREATE POLICY {policy} ON {table} FOR SELECT 
        USING (
            fleet_id = COALESCE(current_setting('app.fleet_id', true), '')::text
        );
        """
        await database.execute(text(policy_sql))
        
        # Enable policy
        await database.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        await database.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))
        print(f"RLS enabled for table {table} with policy {policy}")

    except Exception as e:
        raise RuntimeError(f"Failed to enable RLS on table {table}: {e}")


async def create_table(database: Database, table: str, ddl: str, drop_existing: bool = False) -> None:
    """Create a single table with optional RLS setup."""
    print(f"Creating table '{table}'...")
    try:
        if drop_existing:
            await database.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        # Create table
        await database.execute(text(ddl))

        # Enable RLS if table has fleet_id
        if "fleet_id" in ddl:
            await enable_rls(database, table)

    except Exception as e:
        raise RuntimeError(f"Failed to create table {table}: {e}")


async def setup_database_schema(database: Database, drop_existing: bool = False) -> None:
    """Set up the complete database schema with tables and RLS policies."""
    print("\nSetting up database schema...")

    for table, ddl in CREATE_TABLE_QUERIES.items():
        await create_table(database, table, ddl, drop_existing)

    print("✅ Database schema setup complete!")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_tables_with_fleet_id() -> List[str]:
    """Get list of tables that have fleet_id column and need RLS."""
    return [table for table, ddl in CREATE_TABLE_QUERIES.items() if "fleet_id" in ddl]


def get_partitioned_tables() -> List[str]:
    """Get list of partitioned tables."""
    return PARTITIONED_TABLES.copy()


def get_all_tables() -> List[str]:
    """Get list of all tables in the schema."""
    return list(CREATE_TABLE_QUERIES.keys()) 