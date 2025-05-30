from typing import Any
from databases import Database
from sqlalchemy import text


async def check_role_exists(db: Database, role: str) -> bool:
    """Check if a PostgreSQL role exists."""
    result = await db.fetch_one(
        "SELECT EXISTS (SELECT FROM pg_roles WHERE rolname = :role);",
        {"role": role}
    )
    return result[0] if result else False


async def create_superuser(db: Database) -> None:
    """Create superuser role if it doesn't exist."""
    if not await check_role_exists(db, "superuser"):
        await db.execute("""
            CREATE ROLE superuser 
            WITH LOGIN 
            PASSWORD 'password';
        """)


async def create_end_user(db: Database) -> None:
    """Create end_user role if it doesn't exist."""
    if not await check_role_exists(db, "end_user"):
        await db.execute("""
            CREATE ROLE end_user 
            WITH LOGIN 
            PASSWORD 'password';
        """)


async def grant_permissions(db: Database, db_name: str) -> None:
    """Grant necessary permissions to roles."""
    # Grant permissions to superuser
    await db.execute(f"GRANT CONNECT ON DATABASE {db_name} TO superuser;")
    await db.execute("GRANT USAGE ON SCHEMA public TO superuser;")
    await db.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO superuser;")
    await db.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO superuser;")
    
    # Future table permissions for superuser
    await db.execute("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT ALL PRIVILEGES ON TABLES TO superuser;
    """)
    await db.execute("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT ALL PRIVILEGES ON SEQUENCES TO superuser;
    """)

    # Grant permissions to end_user
    await db.execute(f"GRANT CONNECT ON DATABASE {db_name} TO end_user;")
    await db.execute("GRANT USAGE ON SCHEMA public TO end_user;")
    await db.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO end_user;")
    
    # Future table permissions for end_user
    await db.execute("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT ON TABLES TO end_user;
    """)


async def setup_users_and_permissions(db: Database, db_name: str = "fleetdb") -> None:
    """
    Set up database users and their permissions. Creates two roles:
    - superuser: Has full database access for data import/setup
    - end_user: Has read-only access to all tables
    """
    try:
        await create_superuser(db)
        await create_end_user(db)
        await grant_permissions(db, db_name)
        
    except Exception as e:
        raise RuntimeError(f"Failed to set up users and permissions: {e}")




 