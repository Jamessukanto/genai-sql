import os
import csv
import argparse
import asyncio
from typing import Set, List, Dict, Any
from databases import Database
from sqlalchemy import text

from scripts.setup_data.table_queries import PARTITIONED_TABLES, CREATE_TABLE_QUERIES
from db import create_database_connection


# Define table dependencies (tables that need to be imported first)
TABLE_DEPENDENCIES = {
    'alerts': ['vehicles', 'fleets'],
    'vehicles': ['fleets'],
    'trips': ['vehicles', 'fleets']
}

# Define the order of table imports
IMPORT_ORDER = ['fleets', 'vehicles', 'alerts', 'trips']


async def create_vehicle_partition(db: Database, vehicle_id: str, table: str) -> None:
    """Create a partition for a specific vehicle in a partitioned table."""
    try:
        partition_name = f"{table}_vehicle_{vehicle_id}"
        ddl = f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF {table} FOR VALUES IN ('{vehicle_id}');
        """
        await db.execute(query=ddl)
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
    

async def create_import_functions(db: Database) -> None:
    """Create helper functions for data import."""
    try:
        # Create a function to truncate tables
        await db.execute(query="""
            CREATE OR REPLACE FUNCTION truncate_table(table_name text)
            RETURNS void
            LANGUAGE plpgsql
            SECURITY DEFINER
            SET search_path = public
            AS $$
            BEGIN
                EXECUTE format('TRUNCATE TABLE %I CASCADE', table_name);
            END;
            $$;
        """)

        # Create functions for each table to insert data
        for table in CREATE_TABLE_QUERIES:
            await db.execute(query=f"""
                CREATE OR REPLACE FUNCTION insert_into_{table}(
                    column_names text,
                    values_list text
                )
                RETURNS void
                LANGUAGE plpgsql
                SECURITY DEFINER
                SET search_path = public
                AS $$
                BEGIN
                    EXECUTE 'INSERT INTO {table} (' || column_names || ') VALUES (' || values_list || ')';
                END;
                $$;
            """)
    except Exception as e:
        raise RuntimeError(f"Failed to create import functions: {e}")


def prepare_value(val: Any) -> str:
    """Prepare a value for SQL insertion."""
    if val == '':
        return 'NULL'
    elif isinstance(val, (int, float)):
        return str(val)
    else:
        # Escape single quotes and properly quote string values
        val = str(val).replace("'", "''")
        return f"'{val}'"


async def load_table_data(db: Database, table: str, csv_path: str) -> None:
    """Load data into a table from a CSV file using security definer functions."""
    try:
        if table in PARTITIONED_TABLES:
            vehicle_ids = get_vehicle_ids_from_csv(csv_path)
            for vehicle_id in vehicle_ids:
                await create_vehicle_partition(db, vehicle_id, table)
        
        # Temporarily disable RLS
        await db.execute(query=f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        
        try:
            # Truncate the table using the security definer function
            await db.execute(
                query="SELECT truncate_table(:table_name)",
                values={"table_name": table}
            )
            
            # Read CSV data
            columns, rows = read_csv_data(csv_path)
            if not rows:
                print(f"Warning: No data to import for table {table}")
                return

            print(f"Importing {len(rows)} rows into {table}...")
            
            # Import data in batches
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                for row in batch:
                    try:
                        # Prepare column names and values
                        values = [prepare_value(row.get(col, '')) for col in columns]
                        # Format column names and values as comma-separated strings
                        column_names_str = ', '.join([f'"{col}"' for col in columns])
                        values_str = ', '.join(values)
                        
                        # Use the security definer function to insert
                        await db.execute(
                            query=f"SELECT insert_into_{table}(:column_names, :value_list)",
                            values={"column_names": column_names_str, "value_list": values_str}
                        )
                    except Exception as e:
                        print(f"Error on row: {row}")
                        raise
            
            # Verify the import
            result = await db.fetch_one(f"SELECT COUNT(*) FROM {table}")
            print(f"Imported {result[0]} rows into {table}")
            
        finally:
            # Re-enable RLS
            await db.execute(query=f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            
    except Exception as e:
        raise RuntimeError(f"Failed to load data into table {table}: {e}")




async def import_data(db: Database, csv_dir: str) -> None:
    """Import data from CSV files into the database."""
    print(f"\nImporting data from {csv_dir}...")
    
    # First create the helper functions
    await create_import_functions(db)
    
    # Check which CSV files are available
    available_csvs = {}
    missing_csvs = []
    for table in IMPORT_ORDER:
        if table not in CREATE_TABLE_QUERIES:
            print(f"Warning: Table '{table}' not found in CREATE_TABLE_QUERIES, skipping...")
            continue
            
        csv_path = os.path.join(csv_dir, f"{table}.csv")
        if os.path.exists(csv_path):
            available_csvs[table] = csv_path
        else:
            missing_csvs.append(table)
    
    if not available_csvs:
        raise RuntimeError(f"No valid CSV files found in directory: {csv_dir}")
    
    # Check dependencies before starting any imports
    can_import = True
    for table in available_csvs:
        if table in TABLE_DEPENDENCIES:
            missing_deps = [dep for dep in TABLE_DEPENDENCIES[table] 
                          if dep not in available_csvs]
            if missing_deps:
                print(f"\nError: Cannot import '{table}.csv' - missing required dependencies:")
                for dep in missing_deps:
                    print(f"- {dep}.csv")
                can_import = False
    
    if not can_import:
        print("\nImport cancelled. Please provide all required dependency files and try again.")
        return
    
    # If all dependencies are met, proceed with import
    for table in IMPORT_ORDER:
        if table in available_csvs:
            print(f"\nImporting '{table}'...")
            await load_table_data(db, table, available_csvs[table])
    
    print("\nImport complete!")


async def main(csv_dir: str, db: Database = None) -> None:
    """Import data from CSV files into the database."""
    if not csv_dir:
        raise ValueError("CSV directory path is required")
    print()
    print()
    print()
    print("HA")
    print("csv_dir", csv_dir)
    print("db", db)
    print()




    # csv_dir = os.path.abspath(csv_dir)
    print(csv_dir)
    print("csv_dir after abs", csv_dir)

    print()
    if not os.path.isdir(csv_dir):
        raise ValueError(f"CSV directory does not exist: {csv_dir}")

    try:
        # Initialize database connection
        if not db:
            print("NO DB, creating...")
            db = create_database_connection()
            await db.connect()

        print("csv_dir", csv_dir)
        print("db", db)
        print()
        # Import data
        await import_data(db, csv_dir)
        print("Data import complete!")

    except Exception as e:
        raise RuntimeError(f"Failed to import data: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import data from CSV files into database.")
    parser.add_argument("--csv-dir", required=True, help="Directory containing CSV files")
    args = parser.parse_args()

    asyncio.run(main(args.csv_dir))



