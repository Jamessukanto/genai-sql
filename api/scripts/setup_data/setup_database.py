
import os
import argparse
import asyncio
from databases import Database
from sqlalchemy import text

from scripts.setup_data.table_queries import CREATE_TABLE_QUERIES
from scripts.setup_data.setup_user import setup_users_and_permissions
from scripts.setup_data.import_data import main as import_data


async def verify_db_connection(db: Database) -> None:
    """Verify database connection is working."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}")


async def enable_rls(db: Database, table: str) -> None:
    """Enable row-level security on a table with fleet_id-based isolation."""
    try:
        policy = f"fleet_isolation_{table}"
        await db.execute(text(f"DROP POLICY IF EXISTS {policy} ON {table};"))
        await db.execute(text(
            f"CREATE POLICY {policy} ON {table} FOR SELECT "
            "USING (fleet_id = current_setting('app.fleet_id')::text);"
        ))
        await db.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        await db.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))
    except Exception as e:
        raise RuntimeError(f"Failed to enable RLS on table {table}: {e}")


async def create_table(db: Database, table: str, ddl: str, drop_existing: bool = False) -> None:
    """Create a single table and set up RLS if it contains fleet_id."""
    try:
        if drop_existing:
            await db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        
        await db.execute(text(ddl))
        if "fleet_id" in ddl:
            await enable_rls(db, table)
    except Exception as e:
        raise RuntimeError(f"Failed to create table {table}: {e}")


async def main(drop_existing: bool, csv_dir: str, existing_db: Database = None, db_name: str = None) -> None:
    """Initialize database schema, load data, and set up permissions."""

    # print("existing_db:", existing_db)
    print("db_name:", db_name)

    try:
        # Initialize connection
        db = existing_db or Database(os.getenv("DATABASE_URL"))
        if not existing_db:
            await db.connect()
            await verify_db_connection(db)
            print("Database connection established")

        # Create tables
        print(f"\nSetting up database tables...")
        for table, ddl in CREATE_TABLE_QUERIES.items():
            print(f"Creating table '{table}'...")
            await create_table(db, table, ddl, drop_existing)
        
        # Import data
        print(f"\nImporting data from {csv_dir}...")
        await import_data(db, csv_dir)

        # Set up users and permissions
        print(f"\nSetting up users for database: {db_name}")
        db_name = db_name or "fleetdb"
        await setup_users_and_permissions(db, db_name)

    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        if not existing_db:
            await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database schema and load data.")
    parser.add_argument("--csv-dir", default="/api/data", help="Directory containing CSV files")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing tables")
    parser.add_argument("--db-name", help="Database name to use")
    args = parser.parse_args()

    asyncio.run(main(args.drop_existing, args.csv_dir, db_name=args.db_name))



