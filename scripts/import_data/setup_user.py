import asyncpg


async def setup_users_and_permissions(database_url):
    conn = await asyncpg.connect(database_url)

    try:
        # Create superuser (if not already created)
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_roles WHERE rolname = 'postgres'
                ) THEN
                    CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'postgres';
                END IF;
            END $$;
        """)

        # Create end_user (if not already created)
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_roles WHERE rolname = 'end_user'
                ) THEN
                    CREATE ROLE end_user WITH LOGIN PASSWORD 'end_user_password';
                END IF;
            END $$;
        """)

        # Grant privileges to end_user
        await conn.execute("""
            GRANT CONNECT ON DATABASE fleetdb TO end_user;
            GRANT USAGE ON SCHEMA public TO end_user;
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO end_user;
        """)

        # Grant SELECT on future tables created in the schema
        print("Granting default privileges for future tables...")
        await conn.execute("""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO end_user;
        """)

    finally:
        await conn.close()