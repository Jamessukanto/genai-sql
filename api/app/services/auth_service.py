import base64, json
from fastapi import HTTPException, Header


async def get_user_info(authorization: str = Header(...)) -> dict:
    try:
        parts = authorization.split()
        token_parts = parts[1].split('.')

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        if len(token_parts) != 3:
            raise HTTPException(status_code=401, detail="Malformed JWT token")

        payload_b64 = token_parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(decoded_bytes.decode())

        user = payload.get("sub")
        fleet_id = payload.get("fleet_id")

        if not user:
            raise HTTPException(status_code=401, detail="User (sub) not found in token")
        if not fleet_id:
            raise HTTPException(status_code=401, detail="fleet_id not found in token")

        return {"user": user, "fleet_id": fleet_id}

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

