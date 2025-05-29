import base64, json
# import subprocess
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


# def generate_jwt_token(sub: str, fleet_id: int) -> str:
#     """Generate a JWT token by running an external script."""
#     try:
#         # Run the external script to generate the token
#         result = subprocess.run(
#             [
#                 "python", "scripts/generate_jwt_token.py",
#                 "--sub", sub,
#                 "--fleet_id", str(fleet_id),
#                 "--out_token", "scripts/token.txt"
#             ],
#             check=True,
#             capture_output=True,
#             text=True
#         )
#         # Read the generated token from the output file
#         with open("scripts/token.txt", "r") as token_file:
#             token = token_file.read().strip()
#         return token
#     except subprocess.CalledProcessError as e:
#         # Raise an HTTPException if the subprocess fails
#         raise HTTPException(status_code=500, detail=f"Token generation failed: {e.stderr}")
