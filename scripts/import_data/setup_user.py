async def setup_users_and_permissions(db_con, db_name="fleetdb"):

#     # Create superuser (if not already created)
#     await db_con.execute("""
#         DO $$
#         BEGIN
#             IF NOT EXISTS (
#                 SELECT FROM pg_roles WHERE rolname = 'superuser'
#             ) THEN
#                 CREATE ROLE superuser WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'password';
#             END IF;
#         END $$;
#     """)

#     # Create end_user (if not already created)
#     await db_con.execute("""
#         DO $$
#         BEGIN
#             IF NOT EXISTS (
#                 SELECT FROM pg_roles WHERE rolname = 'end_user'
#             ) THEN
#                 CREATE ROLE end_user WITH LOGIN PASSWORD 'password';
#             END IF;
#         END $$;
#     """)

#     # Grant privileges to end_user
#     await db_con.execute(f"""
#         GRANT CONNECT ON DATABASE {db_name} TO end_user;
#         GRANT USAGE ON SCHEMA public TO end_user;
#         GRANT SELECT ON ALL TABLES IN SCHEMA public TO end_user;
#     """)

#     # Grant SELECT on future tables created in the schema
#     await db_con.execute("""
#         ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO end_user;
#     """)

    # Check and create superuser role
    superuser_exists = await db_con.fetch_one("""
        SELECT EXISTS (
            SELECT FROM pg_roles WHERE rolname = 'superuser'
        );
    """)
    if not superuser_exists[0]:
        await db_con.execute("""
            CREATE ROLE superuser WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'password';
        """)

    # Check and create end_user role
    end_user_exists = await db_con.fetch_one("""
        SELECT EXISTS (
            SELECT FROM pg_roles WHERE rolname = 'end_user'
        );
    """)
    if not end_user_exists[0]:
        await db_con.execute("""
            CREATE ROLE end_user WITH LOGIN PASSWORD 'password';
        """)
    
    # Grant privileges to end_user
    await db_con.execute(f"GRANT CONNECT ON DATABASE {db_name} TO end_user;")
    await db_con.execute("GRANT USAGE ON SCHEMA public TO end_user;")
    await db_con.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO end_user;")

    # Grant SELECT on future tables created in the schema
    await db_con.execute("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO end_user;
    """)