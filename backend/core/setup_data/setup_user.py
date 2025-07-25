from typing import Any
from databases import Database


async def check_role_exists(db: Database, role: str) -> bool:
    """Check if a PostgreSQL role exists."""
    result = await db.fetch_one(
        "SELECT EXISTS (SELECT FROM pg_roles WHERE rolname = :role);",
        {"role": role}
    )
    return result[0] if result else False


async def create_role(db: Database, role: str) -> None:
    """Create a PostgreSQL role if it doesn't exist."""
    if not await check_role_exists(db, role):
        await db.execute(f"""
            CREATE ROLE {role} 
            WITH LOGIN 
            PASSWORD 'password';
        """)


async def grant_role_permissions(db: Database, db_name: str, role: str) -> None:
    """Grant permissions for a specific role."""

    # Get the current database user 
    result = await db.fetch_one("SELECT current_user;")
    current_user = result[0] if result else "postgres"  # db user is postgres in development
    
    # Basic permissions
    await db.execute(f"GRANT {role} TO {current_user};")  # for role switching
    await db.execute(f"GRANT CONNECT ON DATABASE {db_name} TO {role};")
    await db.execute(f"GRANT USAGE ON SCHEMA public TO {role};")
    
    if role == "superuser":
        # Superuser gets all table permissions
        await db.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {role};")
        await db.execute(f"""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
            GRANT ALL PRIVILEGES ON TABLES TO {role};
        """)
    else:
        # Regular user gets read-only permissions
        await db.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {role};")
        await db.execute(f"""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
            GRANT SELECT ON TABLES TO {role};
        """)
        if role == "end_user":
            await db.execute("ALTER ROLE end_user NOSUPERUSER NOBYPASSRLS;")


async def setup_users_and_permissions(db: Database, db_name: str = "fleetdb") -> None:
    """
    Set up permissions for two roles:
    - superuser: Has full database access for data import/setup
    - end_user: Has read-only access to all tables
    """
    try:
        await create_role(db, "superuser")
        await create_role(db, "end_user")
        await grant_role_permissions(db, db_name, "superuser")
        await grant_role_permissions(db, db_name, "end_user")        
    except Exception as e:
        raise RuntimeError(f"Failed to set up users and permissions: {e}")




 