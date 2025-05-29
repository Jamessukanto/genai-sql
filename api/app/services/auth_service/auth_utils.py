from datetime import datetime, timedelta
import jwt


def generate_token(
    subject: str, fleet_id: str, exp_hours: int, secret_key: str
    ) -> str:
    """
    Generate JWT token with specified subject and fleet ID.
    """
    payload = {
        "sub": subject,
        "fleet_id": fleet_id,
        "exp": datetime.utcnow() + timedelta(hours=exp_hours)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


