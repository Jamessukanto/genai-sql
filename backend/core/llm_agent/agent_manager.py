import os
from typing import Dict, Any, Tuple

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
# from langchain.chat_models import init_chat_model  # [MISTRAL]
from sqlalchemy import create_engine, text

from core.llm_agent.agent import build_agent
from core.llm_agent.utils import get_model_config, MODELS
from core.db_con import DATABASE_URL


# Global cache for fleet-based agent instances and their databases
_fleet_agent_cache: Dict[str, Tuple[Any, SQLDatabase]] = {}


async def get_or_create_agent_for_fleet(
    fleet_id: str, user: str, model_name: str = "llama-3.3-70b-versatile"
):
    """Get cached LLM agent for fleet or create new one."""
    cache_key = f"fleet_{fleet_id}:{user}:{model_name}"

    if cache_key in _fleet_agent_cache:
        print(f"Using cached agent: {cache_key}")
        return _fleet_agent_cache[cache_key]

    print(f"Creating new agent: {cache_key}")     
    try:
        model_config = get_model_config(model_name)
        print(f"Model config obtained: {model_config}")
        
        db = create_session_aware_database(user, fleet_id)
        print(f"Database created successfully")

        llm = ChatGroq(
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"],
            api_key=os.getenv("GROQ_API_KEY")
        )
        print(f"LLM created successfully")

        agent = await build_agent(db, llm)
        print(f"Agent built successfully")
        
        _fleet_agent_cache[cache_key] = agent
        print(f"Agent cached successfully")

        return agent
    except Exception as e:
        print(f"Error creating agent: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e


# TODO: Refactor for production

def create_session_aware_database(user: str, fleet_id: str):
    """Creates SQLDatabase with specified role and fleet_id."""    

    engine = create_engine(DATABASE_URL)

    # Set role and fleet_id
    with engine.connect() as con:
        con.execute(text("SET statement_timeout = 10000;"))
        con.execute(text(f"SET ROLE {user};"))
        con.execute(text(f"SET app.fleet_id = '{fleet_id}';"))
        con.commit()  

    database = SQLDatabase(engine)
    return database
