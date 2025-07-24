import os
import ssl
from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from urllib.parse import urlparse, parse_qs
from typing import Optional
import time


def get_database_url() -> str:
    """Get and validate database URL, adding required parameters if missing."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    # Parse the URL to modify SSL parameters
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Keep existing SSL parameters from the URL
    print(f"Connecting to database: {parsed.hostname}")
    return url


def get_ssl_context():
    """Create an SSL context that accepts self-signed certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def create_database_connection(url: Optional[str] = None, max_retries: int = 5, retry_delay: int = 5) -> Database:
    """
    Create a database connection with consistent SSL configuration and retry logic.
    """
    db_url = url or get_database_url()
    ssl_context = get_ssl_context()
    
    for attempt in range(max_retries):
        try:
            return Database(
                db_url,
                min_size=1,
                max_size=4,
                ssl=ssl_context,
            )
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            time.sleep(retry_delay)

# Initialize database connection
DATABASE_URL = get_database_url()
engine: Engine = create_engine(DATABASE_URL)

# Configure database with SSL settings
database = create_database_connection(DATABASE_URL)



