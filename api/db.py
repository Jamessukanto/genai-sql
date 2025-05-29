import os
from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
# from dotenv import load_dotenv

# load_dotenv(override=True) 

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"\napi/db, url: {DATABASE_URL}\n")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is required")

engine: Engine = create_engine(DATABASE_URL)
database = Database(DATABASE_URL)

