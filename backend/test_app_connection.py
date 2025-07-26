#!/usr/bin/env python3
from sqlalchemy import create_engine, text
from core.db_con import get_database_url

def test_app_connection():
    """Test the exact same connection method the app uses."""
    print("Testing app connection method...")
    
    # Create engine the same way the app does
    engine = create_engine(get_database_url())
    
    with engine.connect() as con:
        print("Connected to database")
        
        # Check initial user
        result = con.execute(text("SELECT current_user;"))
        initial_user = result.fetchone()[0]
        print(f"Initial user: {initial_user}")
        
        # Set statement timeout (like the app does)
        con.execute(text("SET statement_timeout = 10000;"))
        print("Set statement timeout")
        
        # Try SET ROLE (like the app does)
        try:
            con.execute(text("SET ROLE end_user;"))
            print("✅ SET ROLE command executed without error")
            
            # Check user after SET ROLE
            result = con.execute(text("SELECT current_user;"))
            new_user = result.fetchone()[0]
            print(f"User after SET ROLE: {new_user}")
            
            if new_user == "end_user":
                print("✅ SET ROLE worked - user is now end_user")
            else:
                print(f"⚠️ SET ROLE didn't work - user is still {new_user}")
                
        except Exception as e:
            print(f"❌ SET ROLE failed: {e}")
        
        # Try to set fleet_id (like the app does)
        try:
            con.execute(text("SET app.fleet_id = '1';"))
            print("✅ SET app.fleet_id worked")
        except Exception as e:
            print(f"❌ SET app.fleet_id failed: {e}")
        
        con.commit()
        print("Committed transaction")

if __name__ == "__main__":
    test_app_connection() 