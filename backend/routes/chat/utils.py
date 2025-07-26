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

    return engine



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
        engine = create_engine(get_database_url())
    else:
        # In development, try role switching
        engine = create_engine(get_database_url(), connect_args={"options": "-c role=end_user"})

    # Apply session variables to the engine
    engine = apply_session_variables_with_engine(engine, user, fleet_id)
    
    return engine