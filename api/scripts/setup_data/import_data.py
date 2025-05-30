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


async def disable_rls(db: Database, table: str) -> None:
    """Temporarily disable RLS on a table."""
    await db.execute(query=f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


async def enable_rls(db: Database, table: str) -> None:
    """Re-enable RLS on a table."""
    await db.execute(query=f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


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
                    -- Direct table access with SECURITY DEFINER privileges
                    EXECUTE format(
                        'INSERT INTO {table} (%s) VALUES (%s)',
                        column_names,
                        values_list
                    );
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
        await disable_rls(db, table)
        
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

            print(f"\nProcessing {len(rows)} rows for table {table}")
            print(f"Columns found: {', '.join(columns)}")
            
            # Import data in batches
            batch_size = 1000
            rows_imported = 0
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                try:
                    for row in batch:
                        # Prepare column names and values
                        values = [prepare_value(row.get(col, '')) for col in columns]
                        # Format column names and values as comma-separated strings
                        column_names_str = ', '.join(columns)
                        values_str = ', '.join(values)
                        
                        # Log the first few rows for debugging
                        if rows_imported < 3:
                            print(f"Sample row {rows_imported + 1}: {values_str}")
                        
                        # Use the security definer function to insert
                        await db.execute(
                            query=f"SELECT insert_into_{table}(:column_names, :value_list)",
                            values={"column_names": column_names_str, "value_list": values_str}
                        )
                        rows_imported += 1
                except Exception as e:
                    print(f"Error importing row in {table}: {e}")
                    print(f"Problematic row values: {values_str}")
                    raise
            
            print(f"Successfully imported {rows_imported} rows into {table}")
            
            # Verify the import
            count_result = await db.fetch_one(f"SELECT COUNT(*) FROM {table}")
            if count_result:
                print(f"Actual row count in {table} after import: {count_result[0]}")
            
        finally:
            # Re-enable RLS
            await enable_rls(db, table)
            
    except Exception as e:
        raise RuntimeError(f"Failed to load data into table {table}: {e}")


def get_importable_tables(available_tables: set, imported_tables: set, dependencies: dict) -> set:
    """
    Find tables that can be imported in the current stage.
    A table is importable if all its dependencies have been imported.
    """
    importable = set()
    for table in available_tables:
        if table in imported_tables:
            continue
        
        # Tables with no dependencies are always importable
        if table not in dependencies:
            importable.add(table)
            continue
            
        # Check if all dependencies are satisfied
        deps = dependencies.get(table, set())
        if deps.issubset(imported_tables):
            importable.add(table)
            
    return importable


async def import_data(db: Database, csv_dir: str) -> None:
    """Import data from CSV files into the database using a staged approach."""
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
            print(f"Note: CSV file not found for table '{table}', skipping...")
    
    if not available_csvs:
        raise RuntimeError(f"No valid CSV files found in directory: {csv_dir}")
    
    print("\nFound the following CSV files:")
    for table in available_csvs:
        print(f"- {table}.csv")
    
    # Convert dependencies to sets for easier handling
    table_dependencies = {
        table: set(deps) for table, deps in TABLE_DEPENDENCIES.items()
    }
    
    # Staged import process
    available_tables = set(available_csvs.keys())
    imported_tables = set()
    stage = 1
    
    while True:
        importable = get_importable_tables(available_tables, imported_tables, table_dependencies)
        if not importable:
            break
            
        print(f"\nStage {stage} - Importing tables: {', '.join(sorted(importable))}")
        for table in sorted(importable):  # Sort for consistent order
            try:
                print(f"\nLoading data into '{table}'...")
                await load_table_data(db, table, available_csvs[table])
                imported_tables.add(table)
            except Exception as e:
                print(f"Failed to import {table}: {e}")
                # Remove failed table from available tables
                available_tables.remove(table)
        
        stage += 1
    
    # Final summary
    print("\nImport Summary:")
    if imported_tables:
        print("Successfully imported tables:")
        for table in sorted(imported_tables):
            print(f"- {table}")
    
    remaining = available_tables - imported_tables
    if remaining:
        print("\nTables that could not be imported (missing dependencies):")
        for table in sorted(remaining):
            deps = table_dependencies.get(table, set())
            missing_deps = deps - imported_tables
            if missing_deps:
                print(f"- {table} (needs: {', '.join(sorted(missing_deps))})")
            else:
                print(f"- {table}")
    
    if missing_csvs:
        print("\nSkipped tables (no CSV file found):")
        for table in sorted(missing_csvs):
            print(f"- {table}")


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



