from urllib.parse import urlparse, urlunparse

import os, csv, argparse, asyncio
from databases import Database
from sqlalchemy import text
from dotenv import load_dotenv

from scripts.import_data.table_queries import CREATE_TABLE_QUERIES, PARTITIONED_TABLES
from scripts.import_data.setup_user import setup_users_and_permissions


async def setup_row_level_security(table: str):
    """Set up Row Level Security (RLS) for a given table."""
    try:
        print(f"Enabled RLS on table '{table}'")
        await db.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        await db.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))

        policy = f"fleet_isolation_{table}"
        await db.execute(text(f"DROP POLICY IF EXISTS {policy} ON {table};"))
        await db.execute(text(
            f"CREATE POLICY {policy} ON {table} FOR SELECT "
            "USING (fleet_id = current_setting('app.fleet_id')::text);"
        ))
    except Exception as e:
        print(f"Error setting up RLS for table '{table}': {e}")


async def create_tables(drops_existing_table: bool = False):
    """Create database tables and set up indexes."""
    try:
        for table, ddl in CREATE_TABLE_QUERIES.items():
            if drops_existing_table:
                print(f"Dropping existing table '{table}'...")
                await db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

            print(f"Creating table '{table}'...")
            await db.execute(text(ddl))

            if "fleet_id" in ddl:
                await setup_row_level_security(table)

    except Exception as e:
        print(f"Error creating tables: {e}")


async def create_partition_for_vehicle(vehicle_id: str, table: str, drops_existing_table: bool = False):
    """Create a partition for a specific vehicle_id."""
    try:
        partition_name = f"{table}_vehicle_{vehicle_id}"
        ddl = f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF {table} FOR VALUES IN ('{vehicle_id}');
        """
        if drops_existing_table:
            print(f"Dropping existing table '{partition_name}'...")
            await db.execute(text(f"DROP TABLE IF EXISTS {partition_name} CASCADE"))

        await db.execute(text(ddl))

    except Exception as e:
        print(f"Error creating partition for vehicle_id '{vehicle_id}': {e}")


async def load_data_from_csv_dir(csv_dir: str):
    """Load data from CSV files into partitioned tables."""
    try:
        for table in CREATE_TABLE_QUERIES.keys():
            path = os.path.join(csv_dir, f"{table}.csv")

            # Create partitioned tables dynamically for each vehicle_id in csv  
            if table in PARTITIONED_TABLES:
                with open(path, "r") as csv_file:
                    reader = csv.DictReader(csv_file)
                    vehicle_ids = set(row["vehicle_id"] for row in reader)
                for vehicle_id in vehicle_ids:
                    await create_partition_for_vehicle(vehicle_id, table, True)

            # Load data into table
            if table not in PARTITIONED_TABLES:
                await db.execute(text(f'TRUNCATE TABLE {table} CASCADE'))
            await db.execute(text(f"COPY {table} FROM '{path}' WITH (FORMAT csv, HEADER true)"))

    except Exception as e:
        print(f"Error loading data for {csv_dir}: {e}")


async def main(drop_existing: bool, csv_dir: str):
    if not os.path.isdir(csv_dir):
        raise ValueError(f"CSV directory does not exist: {csv_dir}")

    for table in CREATE_TABLE_QUERIES.keys():
        if not os.path.isfile(os.path.join(csv_dir, f"{table}.csv")):
            raise ValueError(f"Missing CSV file for table: {table}")
        
    try:
        await db.connect()
        await create_tables(db, drop_existing)
        await load_data_from_csv_dir(db, csv_dir)
        await setup_users_and_permissions(db_url)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import data into the database.")
    parser.add_argument(
        "--csv-dir", 
        default="/data", 
        help="Directory containing CSV files (dir path in db service)"
    )
    parser.add_argument(
        "--drop-existing", 
        action="store_true", 
        dest="drop_existing", 
        help="Drop existing tables before creating new ones (default: False)"
    )
    args = parser.parse_args()

    # Load environment variables
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
    load_dotenv(env_path, override=True)

    # Adjust the database URL for local development
    parsed_url = urlparse(os.getenv("DATABASE_URL"))
    if parsed_url.hostname == "db":
        parsed_url = parsed_url._replace(netloc=parsed_url.netloc.replace("db", "localhost"))
    parsed_url = urlunparse(parsed_url)
    print(f"Adjusted database URL: {parsed_url}\n\n")

    db = Database(parsed_url)

    asyncio.run(
        main(args.drop_existing, args.csv_dir)
    )



