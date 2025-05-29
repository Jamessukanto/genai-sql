import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse

from db import database, engine
from scripts.import_data.import_data import main as import_data_main
from app.services.service_utils import get_user_info


sql_router = APIRouter(prefix="/sql")

class SQLRequest(BaseModel):
    sql: str


@sql_router.post("/execute_sql")
async def execute_sql(req: SQLRequest, user_info: dict = Depends(get_user_info)):
    """Executes a SQL query with role and fleet context applied, returning query results."""

    print("Executing SQL.\n")
    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    try:
        # Set up timeout and role-based authorization with RLS
        async with database.connection() as con:
            await con.execute("SET statement_timeout = 10000;")
            await con.execute(f"SET ROLE {user};")
            await con.execute(f"SET app.fleet_id = '{fleet_id}';")
            
            # Execute the SQL query
            rows = await con.fetch_all(req.sql.strip())

        return {"rows": [dict(r) for r in rows]}

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to execute SQL: {e}"
        )

@sql_router.post("/import_data")
async def import_data():
    """
    Import CSV data into the database.

    Note: This is a programmatic alternative to pgAdmin service and 
          shell access on Render (not available for free tier).
    """
    try:
        # Get the absolute path to the data directory
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data"
        )
        if not os.path.exists(data_dir):
            raise HTTPException(
                status_code=400, detail=f"Data directory not found at {data_dir}"
            )
        
        # Extract database name from DATABASE_URL
        db_url = str(engine.url)
        db_name = urlparse(db_url).path.strip('/')
            
        print(f"Starting data import from {data_dir}, using database '{db_name}")
        await import_data_main(drop_existing=True, csv_dir=data_dir, db_name=db_name)
        return {"status": "success", "message": "Data imported successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to import data: {e}"
        )



