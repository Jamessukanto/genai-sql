from fastapi import HTTPException, APIRouter, Body
from app.services.auth_service.auth_utils import generate_token


router = APIRouter()
auth_router = APIRouter(prefix="/auth")

SECRET_KEY = "test_secret"  # Replace in production


@router.post("/generate_jwt_token")
async def generate_jwt_token(
    sub: str = Body(..., embed=True),
    fleet_id: str = Body(..., embed=True),
    exp_hours: int = Body(1, embed=True)
):
    """
    Endpoint to generate JWT token.
    """
    try:
        token = generate_token(sub, fleet_id, exp_hours, SECRET_KEY)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {e}")

