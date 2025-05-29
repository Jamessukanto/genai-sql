import os
from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

load_dotenv(override=True)  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"\napi/db, url: {DATABASE_URL}\n")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is required")

# database = Database(DATABASE_URL)



# Create a shared SQLAlchemy engine
engine: Engine = create_engine(DATABASE_URL)

# Initialize Database and SQLDatabase using the same engine
database = Database(DATABASE_URL)
# sql_database = SQLDatabase(engine=engine)
print("\n1ENGINE:", engine)

# Pre-warm pool with min_size connections
# database = Database(
#     DATABASE_URL,
#     min_size=4,
#     max_size=10,
# )