from datetime import datetime, timedelta
import argparse, jwt
from fastapi import Header


def generate_token(
    subject: str, fleet_id: str, exp_hours: int, test_secret: str = "test_secret"
    ) -> str:
    """Generate JWT token with specified subject and fleet ID"""
    payload = {
        "sub": subject,
        "fleet_id": fleet_id,
        "exp": datetime.utcnow() + timedelta(hours=exp_hours)
    }
    return jwt.encode(payload, test_secret, algorithm="HS256")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate JWT token for fleet management')
    parser.add_argument('--sub', default='end_user', help='User identifier, default: end_user')
    parser.add_argument('--fleet_id', default='1', help='Fleet ID')
    parser.add_argument("--exp_hours", type=int, default=1)
    parser.add_argument('-o', '--out_token', default='token.txt', help='Output file to save the token, default: token.txt')
    
    args = parser.parse_args()
    
    token = generate_token(args.sub, args.fleet_id, args.exp_hours)    

    with open(args.out_token, 'w') as f:
        f.write(token)
