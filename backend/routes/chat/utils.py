from sqlalchemy import text
from langchain_community.utilities import SQLDatabase
import os


def apply_session_variables_with_engine(engine, user: str, fleet_id: str):
    """
    Ensures the connection pool is initialized with the correct session state.
    """
    with engine.connect() as con:
        con.execute(text("SET statement_timeout = 10000;"))
        
        # Try role switching (works for development)
        try:
            con.execute(text(f"SET ROLE {user};"))
            print(f"✅ Chat: Role switching successful: {user}")
        except Exception as e:
            print(f"⚠️ Chat: Role switching failed (Render environment): {e}")
        
        con.execute(text(f"SET app.fleet_id = '{fleet_id}';"))
        con.commit()  


class SessionAwareSQLDatabase(SQLDatabase):
    """
    A SQLDatabase subclass that ensures session variables are set before each query execution.
    This ensures proper Row-Level Security (RLS) enforcement.
    """
    
    def __init__(self, engine, user: str, fleet_id: str, **kwargs):
        super().__init__(engine, **kwargs)
        self.user = user
        self.fleet_id = fleet_id
    
    def _set_session_variables(self):
        """Set session variables before each query."""
        try:
            super().run(text("SET statement_timeout = 10000;"))
            
            # Try role switching (works for development)
            try:
                super().run(text(f"SET ROLE {self.user};"))
                print(f"✅ SessionAwareSQLDatabase: Role switching successful: {self.user}")
            except Exception as e:
                print(f"⚠️ SessionAwareSQLDatabase: Role switching failed (Render environment): {e}")
            
            super().run(text(f"SET app.fleet_id = '{self.fleet_id}';"))
        except Exception as e:
            print(f"Warning: Failed to set session variables: {e}")
    
    def run(self, command, fetch="all", **kwargs):
        """Override run to ensure session variables are set before each query."""
        self._set_session_variables()
        return super().run(command, fetch, **kwargs)
    
    def get_table_info(self, table_names=None):
        """Override get_table_info to ensure session variables are set."""
        self._set_session_variables()
        return super().get_table_info(table_names)


def create_session_aware_database(user: str, fleet_id: str):
    """
    Creates a SQLDatabase instance with session variable enforcement.
    """
    from sqlalchemy import create_engine
    from core.db_con import get_database_url
    
    # Check if we're in Render environment (where role switching fails)
    is_render = os.getenv("RENDER", "").lower() == "true"
    
    if is_render:
        # In Render, connect directly as end_user if that's what we want
        # For now, use the default connection and skip role switching
        print("🔄 Render environment detected - using direct connection without role switching")
        fleet_engine = create_engine(get_database_url())
    else:
        # In development, try role switching
        fleet_engine = create_engine(get_database_url(), connect_args={"options": "-c role=end_user"})

    
    # Apply session variables to the engine
    apply_session_variables_with_engine(fleet_engine, user, fleet_id)
    
    # Create SQLDatabase with session variable enforcement
    db = SessionAwareSQLDatabase(engine=fleet_engine, user=user, fleet_id=fleet_id)
    
    return db