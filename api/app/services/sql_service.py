from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import database
from app.services.auth_service import get_user_info

sql_router = APIRouter(prefix="/sql")

class SQLRequest(BaseModel):
    sql: str


@sql_router.post("/execute_sql")
async def execute_sql(req: SQLRequest, user_info: dict = Depends(get_user_info)):
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
        raise HTTPException(status_code=400, detail=str(e))
