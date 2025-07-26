#!/usr/bin/env python3
import asyncio
from databases import Database
from core.db_con import get_database_url

async def test_set_role():
    """Test if SET ROLE end_user actually works using the most reliable method."""
    db = Database(get_database_url())
    await db.connect()
    
    try:
        # Check initial state
        result = await db.fetch_one("SELECT current_user;")
        initial_user = result[0]
        print(f"Initial user: {initial_user}")
        
        # Check if end_user role exists
        result = await db.fetch_one("SELECT EXISTS (SELECT FROM pg_roles WHERE rolname = 'end_user');")
        end_user_exists = result[0] if result else False
        print(f"end_user role exists: {end_user_exists}")
        
        # Check what roles the current user can access
        result = await db.fetch_one("""
            SELECT rolname 
            FROM pg_roles 
            WHERE oid IN (
                SELECT roleid 
                FROM pg_auth_members 
                WHERE member = (SELECT oid FROM pg_roles WHERE rolname = current_user)
            );
        """)
        available_roles = [row[0] for row in result] if result else []
        print(f"Roles available to current user: {available_roles}")
        
        # Try SET ROLE
        try:
            await db.execute("SET ROLE end_user;")
            print("✅ SET ROLE command executed without error")
            
            # Verify the change
            result = await db.fetch_one("SELECT current_user;")
            new_user = result[0]
            print(f"User after SET ROLE: {new_user}")
            
            # Check role with SHOW command
            result = await db.fetch_one("SHOW role;")
            current_role = result[0]
            print(f"Current role (SHOW role): {current_role}")
            
            if new_user == "end_user" and current_role == "end_user":
                print("✅ SET ROLE worked - user is now end_user")
            else:
                print(f"⚠️ SET ROLE didn't work - user is still {new_user}, role is {current_role}")
                
        except Exception as e:
            print(f"❌ SET ROLE failed: {e}")
            
            # Try to grant the role manually
            print("\nAttempting to grant end_user role manually...")
            try:
                await db.execute(f"GRANT end_user TO {initial_user};")
                print(f"✅ Granted end_user to {initial_user}")
                
                # Try SET ROLE again
                await db.execute("SET ROLE end_user;")
                print("✅ SET ROLE worked after manual grant")
                
                # Verify
                result = await db.fetch_one("SELECT current_user;")
                print(f"User after manual grant + SET ROLE: {result[0]}")
                
            except Exception as grant_error:
                print(f"❌ Failed to grant role manually: {grant_error}")
            
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_set_role()) 