from fastapi import HTTPException, APIRouter, Body
from datetime import datetime, timedelta
import jwt


auth_router = APIRouter(prefix="/auth")

SECRET_KEY = "test_secret"  # TODO: Refactor in production later


@auth_router.post("/generate_jwt_token")
async def generate_jwt_token(
    sub: str = Body(...),
    fleet_id: str = Body(...),
    exp_hours: int = Body(1)
):
    """
    Endpoint to generate JWT token embedding user and fleet information.
    """
    try:
        payload = {
            "sub": sub,
            "fleet_id": fleet_id,
            "exp": datetime.utcnow() + timedelta(hours=exp_hours)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"token": token}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate JWT: {e}"
        )



# {"alert_id":"1","vehicle_id":"1","alert_type":"HighTemp","severity":"High","alert_ts":"2025-05-14T12:00:00","value":34.1,"threshold":33.0,"resolved_bool":false,"resolved_ts":null}
# {"alert_id":"2","vehicle_id":"2","alert_type":"Overcharge","severity":"Medium","alert_ts":"2025-05-14T10:00:00","value":95.0,"threshold":90.0,"resolved_bool":true,"resolved_ts":"2025-05-14T11:00:00"}
# {"alert_id":"3","vehicle_id":"4","alert_type":"LowSOC","severity":"Medium","alert_ts":"2025-05-14T09:00:00","value":15.0,"threshold":20.0,"resolved_bool":false,"resolved_ts":null},
# {"alert_id":"4","vehicle_id":"5","alert_type":"HighTemp","severity":"Low","alert_ts":"2025-05-14T07:00:00","value":32.0,"threshold":33.0,"resolved_bool":true,"resolved_ts":"2025-05-14T08:00:00"}]}%    



curl -X POST https://genai-sql-1.onrender.com/api/sql/setup
{"status":"success","message":"Database setup and data import completed successfully","details":{"database":"fleetdb_xrco","data_directory":"/opt/render/project/src/api/data"}}%                                                                                                                                                             (cb_sql) ➜  api git:(main) curl -X POST https://genai-sql-1.onrender.com/api/sql/execute -H "Content-Type: application/json" -d '{"sql": "SELECT COUNT(*) FROM fleets"}'
curl -X POST https://genai-sql-1.onrender.com/api/sql/execute -H "Content-Type: application/json" -d '{"sql": "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 200"}'
{"detail":[{"type":"missing","loc":["header","authorization"],"msg":"Field required","input":null}]}%                                                                  (cb_sql) ➜  api git:(main) curl -X POST https://genai-sql-1.onrender.com/api/auth/login -H "Content-Type: application/json" -d '{"username": "end_user", "password": "password"}'
{"detail":"Not Found"}%                                                                                                                                                (cb_sql) ➜  api git:(main) curl -X POST https://genai-sql-1.onrender.com/api/auth/generate_jwt_token -H "Content-Type: application/json" -d '{"sub": "end_user", "fleet_id": "fleet1", "exp_hours": 24}'
{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbmRfdXNlciIsImZsZWV0X2lkIjoiZmxlZXQxIiwiZXhwIjoxNzQ4NjU1MjAxfQ.tkfbc8aPCLL97jehWFBsK76-6KGPFIrK07hr5rrFmxw"}(cb_sql) ➜  api git:(main) curl -X POST https://genai-sql-1.onrender.com/api/sql/execute -H "Content-Type: application/json" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbmRfdXNlciIsImZsZWV0X2lkIjoiZmxlZXQxIiwiZXhwIjoxNzEwODk5NzgyfQ.8vHoTTt_g_V_Ib8_IfxUuL-0nVQXoYXnwYhBHhXVyQE" -d '{"sql": "SELECT * FROM alerts ORDER BY created_at DESC"}'
{"detail":{"status":"error","message":"Failed to execute SQL: permission denied to set role \"end_user\""}}%                                                           (cb_sql) ➜  api git:(main) curl -X POST https://genai-sql-1.onrender.com/api/auth/generate_jwt_token -H "Content-Type: application/json" -d '{"sub": "superuser", "fleet_id": "fleet1", "exp_hours": 24}'
{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcnVzZXIiLCJmbGVldF9pZCI6ImZsZWV0MSIsImV4cCI6MTc0ODY1NTM1Nn0.TitdhnmPNaLK2uBSnLFUzxDYOWjB3DHcSCUZDyXm6vM"}%                                                                                                                                                                     (cb_sql) ➜  api git:(main) ✗ curl -X POST https://genai-sql-1.onrender.com/api/sql/execute -H "Content-Type: application/json" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcnVzZXIiLCJmbGVldF9pZCI6ImZsZWV0MSIsImV4cCI6MTc0ODY1NTM1Nn0.TitdhnmPNaLK2uBSnLFUzxDYOWjB3DHcSCUZDyXm6vM" -d '{"sql": "SELECT * FROM alerts ORDER BY created_at DESC"}'
{"detail":{"status":"error","message":"Failed to execute SQL: column \"created_at\" does not exist"}}%                                                                 (cb_sql) ➜  api git:(main) ✗ curl -X POST https://genai-sql-1.onrender.com/api/sql/execute -H "Content-Type: application/json" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcnVzZXIiLCJmbGVldF9pZCI6ImZsZWV0MSIsImV4cCI6MTc0ODY1NTM1Nn0.TitdhnmPNaLK2uBSnLFUzxDYOWjB3DHcSCUZDyXm6vM" -d '{"sql": "SELECT * FROM alerts"}'                         
{"status":"success","rows":[{"alert_id":"1","vehicle_id":"1","alert_type":"HighTemp","severity":"High","alert_ts":"2025-05-14T12:00:00","value":34.1,"threshold":33.0,"resolved_bool":false,"resolved_ts":null},{"alert_id":"2","vehicle_id":"2","alert_type":"Overcharge","severity":"Medium","alert_ts":"2025-05-14T10:00:00","value":95.0,"threshold":90.0,"resolved_bool":true,"resolved_ts":"2025-05-14T11:00:00"},{"alert_id":"3","vehicle_id":"4","alert_type":"LowSOC","severity":"Medium","alert_ts":"2025-05-14T09:00:00","value":15.0,"threshold":20.0,"resolved_bool":false,"resolved_ts":null},{"alert_id":"4","vehicle_id":"5","alert_type":"HighTemp","severity":"Low","alert_ts":"2025-05-14T07:00:00","value":32.0,"threshold":33.0,"resolved_bool":true,"resolved_ts":"2025-05-14T08:00:00"}]}%                                                  (cb_sql) ➜  api git:(main) ✗ 



