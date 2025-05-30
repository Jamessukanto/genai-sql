import base64, json
from fastapi import HTTPException, Header
import jwt

SECRET_KEY = "test_secret"  # TODO: Refactor in production later

async def get_user_info(authorization: str = Header(...)) -> dict:
    """Parses and validates a JWT to extract user and fleet identifiers."""
    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Invalid Authorization header"
            )
            
        token = parts[1]
        try:
            # Use PyJWT to decode and validate the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user = payload.get("sub")
            fleet_id = payload.get("fleet_id")
            
            if not user:
                raise HTTPException(
                    status_code=401, detail="User (sub) not found in token"
                )
            if not fleet_id:
                raise HTTPException(
                    status_code=401, detail="fleet_id not found in token"
                )

            return {"user": user, "fleet_id": fleet_id}
            
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=401, detail=f"Invalid JWT token: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Invalid JWT: {e}"
        )




