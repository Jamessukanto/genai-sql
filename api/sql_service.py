import json, base64, re
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from api.db import database


sql_router = APIRouter(prefix="/sql")

class SQLRequest(BaseModel):
    sql: str

# Dependency for extracting fleet_id
async def get_fleet_id(authorization: str = Header(...)) -> str:
    try:
        parts = authorization.split()
        token_parts = parts[1].split('.')

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")
        if len(token_parts) != 3:
            raise HTTPException(status_code=401, detail="Malformed JWT token")

        payload_b64 = token_parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(decoded_bytes.decode())

        fleet_id = payload.get("fleet_id")
        if not fleet_id:
            raise HTTPException(status_code=401, detail="fleet_id not found in token")
        return fleet_id

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


@sql_router.post("/execute_sql")
async def execute_sql(req: SQLRequest, fleet_id: str = Depends(get_fleet_id)):
    sql = req.sql.strip()
    print("0"*33)
    # # ... (your safety checks)
    # await database.execute("SET statement_timeout = 10000;")
    # await database.execute(f"SET app.fleet_id = '{fleet_id}';")  # <-- FIXED: plain string formatting
    
    try:
        async with database.connection() as connection:
            await connection.execute("SET statement_timeout = 10000;")
            await connection.execute(f"SET app.fleet_id = '{fleet_id}';")
            rows = await connection.fetch_all(sql)
        return {"rows": [dict(r) for r in rows]}
    
    # try:
    #     rows = await database.fetch_all(sql)
    #     print("\n\n\n\nHEY")
    #     print(dict(rows[0])) #  {'count': 6}

    #     return {"rows": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'\  ' '2 '\ '  '