from urllib.parse import urlparse, urlunparse

import os, csv, argparse, asyncio
from databases import Database
from sqlalchemy import text


from scripts.import_data.table_queries import CREATE_TABLE_QUERIES, PARTITIONED_TABLES
from scripts.import_data.setup_user import setup_users_and_permissions


async def enable_row_level_security(table: str):
    print(f"Enabled RLS on table '{table}'")
    policy = f"fleet_isolation_{table}"
    await db.execute(text(f"DROP POLICY IF EXISTS {policy} ON {table};"))
    await db.execute(text(
        f"CREATE POLICY {policy} ON {table} FOR SELECT "
        "USING (fleet_id = current_setting('app.fleet_id')::text);"
    ))
    await db.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
    await db.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))


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
                await enable_row_level_security(table)

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


async def main(drop_existing: bool, csv_dir: str, existing_db: Database = None):
    csv_dir = os.path.abspath(csv_dir)

    if not os.path.isdir(csv_dir):
        raise ValueError(f"CSV directory does not exist: {csv_dir}")

    try:
        global db
        if existing_db:
            db = existing_db
        else:
            db_url = os.getenv("DATABASE_URL")
            db = Database(db_url)
            await db.connect()
            
        await create_tables(drop_existing)
        await load_data_from_csv_dir(csv_dir)
        await setup_users_and_permissions(db, "fleetdb")
    finally:
        if not existing_db:
            await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create database; import data; set up users.")
    parser.add_argument(
        "--csv-dir", 
        default="/api/data", 
        help="Directory containing CSV files"
    )
    parser.add_argument(
        "--drop-existing", 
        action="store_true", 
        dest="drop_existing", 
        help="Drop existing tables, default: False"
    )
    args = parser.parse_args()

    asyncio.run(
        main(args.drop_existing, args.csv_dir)
    )



