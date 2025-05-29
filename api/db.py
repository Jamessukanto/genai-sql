import os
import ssl
from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from typing import Optional

# load_dotenv(override=True)

def get_database_url() -> str:
    """Get and validate database URL, adding required parameters if missing."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    # Parse the URL to modify SSL parameters
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Update SSL parameters for Render's PostgreSQL
    # Use require mode which verifies SSL is used but doesn't verify certificates
    ssl_params = {
        'sslmode': 'require'  # Only require SSL without certificate verification
    }
    
    # Update or add SSL parameters
    for key, value in ssl_params.items():
        params[key] = [value]
    
    # Reconstruct the URL with updated parameters
    new_query = urlencode(params, doseq=True)
    new_url = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, 
         parsed.params, new_query, parsed.fragment)
    )

    print(f"Connecting to database: {parsed.hostname}")
    return new_url

def get_ssl_context():
    """Create an SSL context that accepts self-signed certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def create_database_connection(url: Optional[str] = None, **kwargs) -> Database:
    """
    Create a database connection with consistent SSL configuration.
    
    Args:
        url: Optional database URL. If not provided, uses DATABASE_URL from environment
        **kwargs: Additional arguments to pass to Database constructor
    
    Returns:
        Database: Configured database connection
    """
    db_url = url or get_database_url()
    ssl_context = get_ssl_context()
    
    return Database(
        db_url,
        min_size=1,
        max_size=4,
        ssl=ssl_context,
        **kwargs
    )

# Initialize database connection
DATABASE_URL = get_database_url()
engine: Engine = create_engine(DATABASE_URL)

# Configure database with SSL settings
database = create_database_connection(DATABASE_URL)

