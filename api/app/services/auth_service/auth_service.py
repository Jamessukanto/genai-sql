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


