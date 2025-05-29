from sqlalchemy import text
from langchain_community.utilities import SQLDatabase


def apply_session_variables_with_engine(engine, user: str, fleet_id: str):
    """
    Ensures the connection pool is initialized with the correct session state.
    """
    with engine.connect() as con:
        con.execute(text("SET statement_timeout = 10000;"))
        con.execute(text(f"SET ROLE '{user}';"))
        con.execute(text(f"SET app.fleet_id = '{fleet_id}';"))


def apply_session_variables_with_sql_database(db: SQLDatabase, user: str, fleet_id: str):
    """
    Ensures the specific connection used by SQLDatabase has the correct session state.
    """
    db.run("SET statement_timeout = 10000;")
    db.run(f"SET ROLE '{user}';")
    db.run(f"SET app.fleet_id = '{fleet_id}';")
