import os
import asyncio
import csv

from typing import Set
from databases import Database
from sqlalchemy import text

from scripts.import_data.table_queries import CREATE_TABLE_QUERIES, PARTITIONED_TABLES


async def create_vehicle_partition(db: Database, vehicle_id: str, table: str) -> None:
    """Create a partition for a specific vehicle in a partitioned table."""
    try:
        partition_name = f"{table}_vehicle_{vehicle_id}"
        ddl = f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF {table} FOR VALUES IN ('{vehicle_id}');
        """
        await db.execute(text(ddl))
    except Exception as e:
        raise RuntimeError(f"Failed to create partition for vehicle {vehicle_id} in table {table}: {e}")


def get_vehicle_ids_from_csv(csv_path: str) -> Set[str]:
    """Extract unique vehicle IDs from a CSV file."""
    try:
        with open(csv_path, "r") as csv_file:
            reader = csv.DictReader(csv_file)
            if "vehicle_id" not in reader.fieldnames:
                raise ValueError(f"CSV file {csv_path} missing vehicle_id column")
            return set(row["vehicle_id"] for row in reader)
    except Exception as e:
        raise RuntimeError(f"Failed to read vehicle IDs from {csv_path}: {e}")


async def load_table_data(db: Database, table: str, csv_path: str) -> None:
    """Load data into a table from a CSV file, handling partitioning if needed."""
    try:
        if table in PARTITIONED_TABLES:
            vehicle_ids = get_vehicle_ids_from_csv(csv_path)
            for vehicle_id in vehicle_ids:
                await create_vehicle_partition(db, vehicle_id, table)
        else:
            await db.execute(text(f'TRUNCATE TABLE {table} CASCADE'))
        
        await db.execute(text(f"COPY {table} FROM '{csv_path}' WITH (FORMAT csv, HEADER true)"))
    except Exception as e:
        raise RuntimeError(f"Failed to load data into table {table}: {e}")


async def main(db: Database, csv_dir: str) -> None:
    """Load data into all tables from corresponding CSV files in a directory."""
    try:
        csv_dir = os.path.abspath(csv_dir)
        if not os.path.isdir(csv_dir):
            raise ValueError(f"CSV directory does not exist: {csv_dir}")

        for table in CREATE_TABLE_QUERIES:
            csv_path = os.path.join(csv_dir, f"{table}.csv")
            if not os.path.exists(csv_path):
                print(f"Warning: CSV file not found for table {table}")
                continue
            print(f"Loading data into '{table}'...")
            await load_table_data(db, table, csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to import data from CSV dir: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSV data into database tables.")
    parser.add_argument(
        "--csv-dir", type=str, required=True, help="Directory containing CSV files"
    )
    args = parser.parse_args()

    # print("existing_db:", existing_db)
    print("db_name:", db_name)

    try:
        # Initialize connection
        db = existing_db or Database(os.getenv("DATABASE_URL"))
        if not existing_db:
            await db.connect()
            await verify_db_connection(db)
            print("Database connection established")
    except Exception as e:
        print(f"Connection error: {e}")

    asyncio.run(main(db, args.csv_dir))

