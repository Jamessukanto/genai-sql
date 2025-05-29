import os
from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

load_dotenv(override=True)

def get_database_url() -> str:
    """Get and validate database URL, adding required parameters if missing."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    # Parse the URL to add SSL mode if not present
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Add SSL requirements for Render's PostgreSQL
    if 'sslmode' not in params:
        if parsed.query:
            url = f"{url}&sslmode=require"
        else:
            url = f"{url}?sslmode=require"

    print(f"Connecting to database: {parsed.hostname}")
    return url

# Initialize database connection
DATABASE_URL = get_database_url()
engine: Engine = create_engine(DATABASE_URL)
database = Database(
    DATABASE_URL,
    min_size=1,
    max_size=10,
    ssl=True
)

