import os
import csv
import hmac
import argparse
import asyncio
from typing import Set, List, Dict, Any, Optional
from databases import Database

from core.setup_database.schema import PARTITIONED_TABLES, CREATE_TABLE_QUERIES
from core.db_con import database

# Data loading batch size
IMPORT_DATA_BATCH_SIZE = 1000

# Define table dependencies (tables that need to be imported first)
TABLE_DEPENDENCIES = {
    'alerts': ['vehicles', 'fleets'],
    'vehicles': ['fleets'],
    'trips': ['vehicles', 'fleets']
}

# Define the order of table imports
IMPORT_ORDER = ['fleets', 'vehicles', 'alerts', 'trips']


async def create_vehicle_partition(database: Database, vehicle_id: str, table: str) -> None:
    """Create a partition for a specific vehicle in a partitioned table."""
    try:
        partition_name = f"{table}_vehicle_{vehicle_id}"
        ddl = f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF {table} FOR VALUES IN ('{vehicle_id}');
        """
        await database.execute(query=ddl)
    except Exception as e:
        raise RuntimeError(f"Failed to create partition for vehicle {vehicle_id} in table {table}: {e}")


def get_vehicle_ids_from_csv(csv_path: str) -> Set[str]:
    """Extract unique vehicle IDs from a CSV file.
    
    This function uses constant-time comparison when checking for the required column
    to prevent timing attacks.
    
    Args:
        csv_path: Path to the CSV file containing vehicle data
        
    Returns:
        Set of unique vehicle IDs from the CSV
        
    Raises:
        ValueError: If the vehicle_id column is missing
        RuntimeError: If there are issues reading the file
    """
    try:
        with open(csv_path, "r") as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                raise ValueError(f"CSV file {csv_path} has no headers")
                
            # Use constant-time comparison to check for vehicle_id column
            has_vehicle_id = False
            for field in reader.fieldnames:
                if hmac.compare_digest(field, "vehicle_id"):
                    has_vehicle_id = True
                    break
                    
            if not has_vehicle_id:
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
    

async def create_import_functions(database: Database) -> None:
    """Create helper functions for data import."""
    try:
        # Create a function to truncate tables
        await database.execute(query="""
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
            await database.execute(query=f"""
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


async def load_table_data(database: Database, table: str, csv_path: str) -> None:
    """Load data into a table from a CSV file using security definer functions."""
    try:
        if table in PARTITIONED_TABLES:
            vehicle_ids = get_vehicle_ids_from_csv(csv_path)
            for vehicle_id in vehicle_ids:
                await create_vehicle_partition(database, vehicle_id, table)
        
        # Temporarily disable RLS
        await database.execute(query=f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        
        try:
            # Truncate the table using the security definer function
            await database.execute(
                query="SELECT truncate_table(:table_name)",
                values={"table_name": table}
            )
            
            # Import data in batches
            columns, rows = read_csv_data(csv_path)

            for i in range(0, len(rows), IMPORT_DATA_BATCH_SIZE):
                batch = rows[i:i + IMPORT_DATA_BATCH_SIZE]
                for row in batch:
                    try:
                        # Prepare column names and values
                        values = [prepare_value(row.get(col, '')) for col in columns]
                        # Format column names and values as comma-separated strings
                        column_names_str = ', '.join([f'"{col}"' for col in columns])
                        values_str = ', '.join(values)
                        
                        # Use the security definer function to insert
                        await database.execute(
                            query=f"SELECT insert_into_{table}(:column_names, :value_list)",
                            values={"column_names": column_names_str, "value_list": values_str}
                        )
                    except Exception as e:
                        print(f"Error on row: {row}")
                        raise
            
            # Verify the number of imported rows
            result = await database.fetch_one(f"SELECT COUNT(*) FROM {table}")
            if len(rows) != result[0]:
                e = f"Imported {result[0]} rows into {table}. Expected: {len(rows)} rows."
                raise RuntimeError(f"Failed to load data into table {table}: {e}")
    
        finally:
            # Re-enable RLS
            await database.execute(query=f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            
    except Exception as e:
        raise RuntimeError(f"Failed to load data into table {table}: {e}")


async def import_data(database: Database, csv_dir: str) -> None:
    """Import data from CSV files into the database."""
    print(f"\nImporting data from {csv_dir}...")
    
    # First create the helper functions
    await create_import_functions(database)
    
    # Check which CSV files are available
    available_csvs = {}
    missing_csvs = []

    for table in CREATE_TABLE_QUERIES:            
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
    for table in CREATE_TABLE_QUERIES:
        if table in available_csvs:
            print(f"\nImporting '{table}'...")
            await load_table_data(database, table, available_csvs[table])
    
    print("\nImport complete!")


async def main(csv_dir: str, database: Database = database) -> None:
    """Import data from CSV files into the database."""
    if not csv_dir:
        raise ValueError("CSV directory path is required")

    csv_dir = os.path.abspath(csv_dir)
    if not os.path.isdir(csv_dir):
        raise ValueError(f"\nCSV directory does not exist: {csv_dir}\n")

    try:
        await database.connect()
        await import_data(database, csv_dir)
        print("Data import complete!")

    except Exception as e:
        raise RuntimeError(f"Failed to import data: {e}")
    finally:
        await database.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import data from CSV files into database.")
    parser.add_argument("--csv-dir", required=True, help="Directory containing CSV files")
    args = parser.parse_args()

    asyncio.run(main(args.csv_dir))



