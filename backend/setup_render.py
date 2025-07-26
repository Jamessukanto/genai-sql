#!/usr/bin/env python3

import subprocess
import sys
import time
import os
import uvicorn

def run_command(cmd, description):
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    # Run commands from the backend directory to ensure proper Python path
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="/opt/render/project/src/backend")

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        print(f"Return code: {result.returncode}")
        sys.exit(1)
    print(f"Success: {description}")

    if result.stdout:
        print(f"Output: {result.stdout}")


def check_database_setup():
    """Check if database is already set up by trying to connect"""
    try:
        import asyncio
        from core.db_con import database
        
        async def test_connection():
            await database.connect()
            # Try a simple query to see if tables exist
            result = await database.fetch_one("SELECT 1")
            await database.disconnect()
            return True
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_connection())
        loop.close()
        return result
    except Exception as e:
        print(f"Database check failed: {e}")
        return False


def main():
    print("Setting up database...")

    # Setup tables, roles with RLS
    print("=== Starting database setup ===")
    run_command(
        "python -m core.setup_database.setup_database --drop-existing --database-name genai_sql_2_postgres",
        "Database setup"
    )
    print("=== Database setup completed ===")

    # Seed data
    print("=== Starting data seeding ===")
    run_command(
        "python -m core.setup_database.import_data --csv-dir ./data",
        "Database seeding"
    )
    print("=== Data seeding completed ===")

    # Verify roles were created
    print("=== Verifying role setup ===")
    run_command(
        "python check_roles.py",
        "Role verification"
    )
    print("=== Role verification completed ===")

    # Start server
    print("\n\nStarting Uvicorn server on 0.0.0.0:8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
    

if __name__ == "__main__":
    main() 

