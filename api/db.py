import os
from databases import Database
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is required")

# Pre-warm pool with min_size connections
database = Database(
    DATABASE_URL,
    min_size=4,
    max_size=10,
)