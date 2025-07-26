import os
import ssl
from databases import Database
from sqlalchemy import create_engine
from typing import Optional, Union
import time


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    print(f"Connecting to database: {url}")
    return url

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def get_connection_config():
    return {
        "min_connections": 1,
        "max_connections": 4,
        "ssl_context": get_ssl_context()
    }

def create_connection(
    url: Optional[str] = None, 
    config: Optional[dict] = get_connection_config(),
    retry_delay: int = 2,
    max_retries: int = 3
) -> Union[Database, create_engine]:
    """Connection factory with consistent SSL configuration and retry logic."""
    db_url = url or get_database_url()

    for attempt in range(max_retries):
        try:
            database = Database(
                db_url,
                min_size=config["min_connections"],
                max_size=config["max_connections"],
                ssl=config["ssl_context"],
            )
            engine = create_engine(
                db_url,
                pool_size=config["min_connections"],
                max_overflow=config["max_connections"] - config["min_connections"],
                connect_args={"sslmode": "require", "sslcert": None, "sslkey": None}
            )
            return database, engine

        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to connect to database after {max_retries} attempts: {e}")
            print(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(retry_delay)


database, engine = create_connection()




