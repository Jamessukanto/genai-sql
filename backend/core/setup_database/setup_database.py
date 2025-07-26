import argparse
import asyncio
from databases import Database
from typing import Optional
import os

from core.setup_database.schema import setup_database_schema
from core.setup_database.roles import RoleManager
from core.db_con import database


async def main(
    drop_existing: bool = False,
    database: Optional[Database] = database,
    database_name: Optional[str] = None
) -> None:
    """Set up database schema and set up roles."""
    try:
        print(f"Setting up database with database connection: {database}, name: {database_name}")

        # Get database name
        if database_name is None:
            from urllib.parse import urlparse
            url = os.getenv("DATABASE_URL")
            if url:
                parsed = urlparse(url)
                database_name = parsed.path.lstrip('/')
            else:
                database_name = "fleetdb"  # fallback
        
        await database.connect()

        # Set up schema (tables + RLS)
        await setup_database_schema(
            database, drop_existing
        )

        # Set up roles
        await RoleManager().setup_roles(
            database, database_name, ["superuser", "end_user"]
        )

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



