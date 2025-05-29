import os
import csv
import argparse
import asyncio
from typing import Set, List, Dict, Any
from databases import Database
from sqlalchemy import text

from scripts.setup_data.table_queries import PARTITIONED_TABLES
from db import create_database_connection


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


def read_csv_data(csv_path: str) -> tuple[List[str], List[Dict[str, Any]]]:
    """Read CSV file and return column names and data rows."""
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames or []
            rows = [row for row in reader]
            return columns, rows
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV file {csv_path}: {e}")


def create_insert_query(table: str, columns: List[str], rows: List[Dict[str, Any]], batch_size: int = 1000) -> List[str]:
    """Create INSERT statements for the data, batching for better performance."""
    queries = []
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        values_list = []
        
        for row in batch:
            # Handle NULL values and escape strings
            values = []
            for col in columns:
                val = row.get(col, '')
                if val == '':
                    values.append('NULL')
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    # Escape single quotes and properly quote string values
                    val = str(val).replace("'", "''")
                    values.append(f"'{val}'")
            
            values_list.append(f"({', '.join(values)})")
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES {', '.join(values_list)};
        """
        queries.append(query)
    
    return queries


async def load_table_data(db: Database, table: str, csv_path: str) -> None:
    """Load data into a table from a CSV file using INSERT statements."""
    try:
        if table in PARTITIONED_TABLES:
            vehicle_ids = get_vehicle_ids_from_csv(csv_path)
            for vehicle_id in vehicle_ids:
                await create_vehicle_partition(db, vehicle_id, table)
        else:
            await db.execute(text(f'TRUNCATE TABLE {table} CASCADE'))
        
        # Read CSV data
        columns, rows = read_csv_data(csv_path)
        if not rows:
            print(f"Warning: No data to import for table {table}")
            return

        # Create and execute INSERT statements in batches
        queries = create_insert_query(table, columns, rows)
        for query in queries:
            await db.execute(text(query))
            
    except Exception as e:
        raise RuntimeError(f"Failed to load data into table {table}: {e}")


async def import_data(db: Database, csv_dir: str) -> None:
    """Import data from CSV files into database tables."""
    print(f"\nImporting data from {csv_dir}...")
    from scripts.setup_data.table_queries import CREATE_TABLE_QUERIES
    
    for table in CREATE_TABLE_QUERIES:
        csv_path = os.path.join(csv_dir, f"{table}.csv")
        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found for table {table}")
            continue
        print(f"Loading data into '{table}'...")
        await load_table_data(db, table, csv_path)


async def main(csv_dir: str, existing_db: Database = None) -> None:
    """Import data from CSV files into the database."""
    if not csv_dir:
        raise ValueError("CSV directory path is required")
    
    csv_dir = os.path.abspath(csv_dir)
    if not os.path.isdir(csv_dir):
        raise ValueError(f"CSV directory does not exist: {csv_dir}")

    try:
        # Initialize database connection
        db = existing_db
        if not db:
            db = create_database_connection()
            await db.connect()

        # Import data
        await import_data(db, csv_dir)
        print("Data import complete!")

    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        if not existing_db and db:
            await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import data from CSV files into database.")
    parser.add_argument("--csv-dir", required=True, help="Directory containing CSV files")
    args = parser.parse_args()

    asyncio.run(main(args.csv_dir))

