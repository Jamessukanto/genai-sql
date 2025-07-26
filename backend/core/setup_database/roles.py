from typing import Any, Protocol
from databases import Database


class RoleStrategy(Protocol):
    """Protocol for role creation strategies."""
    async def create_role(self, db: Database, db_name: str, db_user: str) -> None:
        """Create a role with specific permissions."""
        ...


class SuperuserRole:
    """Strategy for creating superuser role with full permissions."""
    
    async def create_role(self, db: Database, db_name: str, db_user: str) -> None:
        """Create superuser with full database access."""
        await db.execute(f"""
            CREATE ROLE superuser 
            WITH LOGIN 
            PASSWORD 'password'
            SUPERUSER 
            CREATEDB 
            CREATEROLE 
            INHERIT 
            REPLICATION;
        """)
        
        # Grant role switching
        await db.execute(f"GRANT superuser TO {db_user};")
        
        # Grant all permissions (one statement per call)
        await db.execute(f"GRANT CONNECT ON DATABASE \"{db_name}\" TO superuser;")
        await db.execute(f"GRANT USAGE ON SCHEMA public TO superuser;")
        await db.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO superuser;")
        await db.execute(f"""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
            GRANT ALL PRIVILEGES ON TABLES TO superuser;
        """)


class EndUserRole:
    """Strategy for creating end_user role with read-only permissions."""
    
    async def create_role(self, db: Database, db_name: str, db_user: str) -> None:
        """Create end_user with read-only access and RLS enforcement."""
        await db.execute(f"""
            CREATE ROLE end_user 
            WITH LOGIN 
            PASSWORD 'password'
            NOSUPERUSER 
            NOBYPASSRLS 
            NOCREATEDB 
            NOCREATEROLE 
            INHERIT 
            NOREPLICATION;
        """)
        
        # Grant role switching
        await db.execute(f"GRANT end_user TO {db_user};")
        
        # Grant read-only permissions (one statement per call)
        await db.execute(f"GRANT CONNECT ON DATABASE \"{db_name}\" TO end_user;")
        await db.execute(f"GRANT USAGE ON SCHEMA public TO end_user;")
        await db.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO end_user;")
        await db.execute(f"""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
            GRANT SELECT ON TABLES TO end_user;
        """)


class RoleManager:
    """Manages role creation using strategy pattern."""
    
    def __init__(self):
        self.strategies: dict[str, RoleStrategy] = {
            "superuser": SuperuserRole(),
            "end_user": EndUserRole()
        }
    
    async def check_role_exists(self, db: Database, role: str) -> bool:
        """Check if a PostgreSQL role exists."""
        result = await db.fetch_one(
            "SELECT EXISTS (SELECT FROM pg_roles WHERE rolname = :role);",
            {"role": role}
        )
        return result[0] if result else False
    
    async def create_role(self, db: Database, db_name: str, role: str) -> None:
        """Create a role using the appropriate strategy."""
        if await self.check_role_exists(db, role):
            print(f"Role {role} already exists, skipping creation")
            return
        
        if role not in self.strategies:
            raise ValueError(f"No strategy found for role: {role}")
        
        # Get database user for role granting
        result = await db.fetch_one("SELECT current_user;")
        self.db_user = result[0] if result else "postgres"
        
        # Create role
        await self.strategies[role].create_role(db, db_name, self.db_user)
        print(f"✅ Created role '{role}'")
    
    async def setup_roles(self, db: Database, db_name: str, roles: list[str] = None) -> None:
        """Set up specified roles using their respective strategies."""
        if roles is None:
            # Default to all available roles
            roles = list(self.strategies.keys())
        
        try:
            for role in roles:
                if role not in self.strategies:
                    print(f"⚠️ Warning: No strategy found for role '{role}', skipping")
                    continue
                await self.create_role(db, db_name, role)
            
        except Exception as e:
            raise RuntimeError(f"Failed to set up users and permissions: {e}")
    


 