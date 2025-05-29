from fastapi import HTTPException, APIRouter, Body
from datetime import datetime, timedelta
import jwt


auth_router = APIRouter(prefix="/auth")

SECRET_KEY = "test_secret"  # Replace in production later


@auth_router.post("/generate_jwt_token")
async def generate_jwt_token(
    sub: str = Body(...),
    fleet_id: str = Body(...),
    exp_hours: int = Body(1)
):
    """
    Endpoint to generate JWT token.
    """
    try:
        print("generate_jwt_token endpoint!")

        payload = {
            "sub": sub,
            "fleet_id": fleet_id,
            "exp": datetime.utcnow() + timedelta(hours=exp_hours)
        }
        print(f"Payload for JWT: {payload.get('sub')}")
        print(f"Payload for JWT: {payload.get('fleet_id')}")


        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"token": token}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate token: {e}"
        )
