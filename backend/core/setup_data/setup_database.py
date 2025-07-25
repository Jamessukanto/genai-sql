import argparse
import asyncio
from databases import Database
from sqlalchemy import text
from typing import Optional

from core.setup_data.table_queries import CREATE_TABLE_QUERIES
from core.setup_data.setup_user import setup_users_and_permissions
from core.db_con import database


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


async def setup_database_schema(database: Database, drop_existing: bool = False) -> None:
    print("\nSetting up database tables...")

    for table, ddl in CREATE_TABLE_QUERIES.items():
        print(f"Creating table '{table}'...")
        try:
            if drop_existing:
                await database.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

            # Create table
            await database.execute(text(ddl))

            if "fleet_id" in ddl:
                await enable_rls(database, table)

        except Exception as e:
            raise RuntimeError(f"Failed to create table {table}: {e}")


async def main(
    drop_existing: bool = False,
    database: Optional[Database] = database,
    database_name: Optional[str] = "fleetdb"
) -> None:
    """Set up database schema and configure permissions."""
    try:
        print(f"Setting up database with database connection: {database}, database_name: {database_name}")
        await database.connect()
        await setup_database_schema(database, drop_existing)
        await setup_users_and_permissions(database, database_name or "fleetdb")
        print("Database setup complete!")

    except Exception as e:
        raise RuntimeError(f"Failed to set up database: {e}")
    finally:
        await database.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database schema.")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing tables")
    parser.add_argument("--database-name", help="Database name to use")
    args = parser.parse_args()

    asyncio.run(main(args.drop_existing, database_name=args.database_name))



