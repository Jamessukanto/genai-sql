import argparse
import asyncio
from databases import Database
from sqlalchemy import text
from typing import Optional

from core.setup_data.table_queries import CREATE_TABLE_QUERIES
from core.setup_data.setup_user import setup_users_and_permissions
from core.db_con import create_database_connection


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
        
        # Create a more explicit RLS policy with better error handling
        policy_sql = f"""
        CREATE POLICY {policy} ON {table} FOR SELECT 
        USING (
            fleet_id = COALESCE(current_setting('app.fleet_id', true), '')::text
        );
        """
        await db.execute(text(policy_sql))
        
        await db.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        await db.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))
        
        print(f"RLS enabled for table {table} with policy {policy}")
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


async def setup_database_schema(
    db: Database,
    drop_existing: bool = False,
    db_name: Optional[str] = None
) -> None:
    """Set up database schema only, without importing data."""
    print("\nSetting up database tables...")
    for table, ddl in CREATE_TABLE_QUERIES.items():
        print(f"Creating table '{table}'...")
        await create_table(db, table, ddl, drop_existing)


async def main(
    drop_existing: bool = False,
    db: Optional[Database] = None,
    db_name: Optional[str] = "fleetdb"
) -> None:
    """Set up database schema and configure permissions."""
    try:
        print(f"Setting up database with db connection: {db}, db_name: {db_name}")
        if not db:
            db = create_database_connection()
            await db.connect()

        await verify_db_connection(db)
        await setup_database_schema(db, drop_existing)
        await setup_users_and_permissions(db, db_name or "fleetdb")
        print("Database setup complete!")

    except Exception as e:
        print(f"\nFailed setting up database. Error: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database schema.")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing tables")
    parser.add_argument("--db-name", help="Database name to use")
    args = parser.parse_args()

    asyncio.run(main(args.drop_existing, db_name=args.db_name))



