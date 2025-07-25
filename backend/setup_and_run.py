#!/usr/bin/env python3
import subprocess
import sys
import time
import os

def run_command(cmd, description):
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
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
    # 1. Check if database is already set up
    if check_database_setup():
        print("Database already set up, skipping setup...")
    else:
        print("Database not set up, running setup...")
        run_command("python core/setup_data/setup_database.py", "Database setup")
        run_command("python core/setup_data/import_data.py --csv-dir ./data", "Database seeding")
    
    # 2. Start the app
    run_command("uvicorn main:app --host 0.0.0.0 --port 8000", "Starting FastAPI server")

if __name__ == "__main__":
    main() 


    # setup_database --drop-existing // import_data --csv-dir ./data