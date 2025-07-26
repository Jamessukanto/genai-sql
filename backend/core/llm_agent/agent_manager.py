import os
import traceback
from typing import Dict, Any, Tuple

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
# from langchain.chat_models import init_chat_model  # [MISTRAL]
from sqlalchemy import text

from core.llm_agent.agent import build_agent
from core.llm_agent.utils import get_model_config, MODELS
from core.db_con import engine


# Global cache for fleet-based agent instances and their databases
_fleet_agent_cache: Dict[str, Tuple[Any, SQLDatabase]] = {}


def clear_agent_cache():
    """Clear the agent cache to force fresh connections."""
    global _fleet_agent_cache
    _fleet_agent_cache.clear()
    print("Agent cache cleared")


async def get_or_create_agent_for_fleet(
    fleet_id: str, user: str, model_name: str = "llama-3.3-70b-versatile"
):
    """Get cached LLM agent for fleet or create new one."""
    cache_key = f"fleet_{fleet_id}:{user}:{model_name}"

    # Clear cache if this is a different fleet than what's cached
    cached_fleets = [key.split(':')[0] for key in _fleet_agent_cache.keys()]
    current_fleet = f"fleet_{fleet_id}"

    if cached_fleets and current_fleet not in cached_fleets:
        print(f"Fleet changed to {fleet_id}, clearing cache")
        clear_agent_cache()

    if cache_key in _fleet_agent_cache:
        print(f"Using cached agent: {cache_key}")
        return _fleet_agent_cache[cache_key]

    print(f"Creating new agent: {cache_key}")     
    try:
        model_config = get_model_config(model_name)        
        db = create_session_aware_SQLdatabase(engine, user, fleet_id)
        llm = ChatGroq(
            model=model_config["model"],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"],
            api_key=os.getenv("GROQ_API_KEY")
        )

        agent = await build_agent(db, llm)
        
        _fleet_agent_cache[cache_key] = agent
        return agent
        
    except Exception as e:
        print(f"Error creating agent: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise e


# TODO: Refactor for production
def create_session_aware_SQLdatabase(engine, user: str, fleet_id: str):
    """Creates SQLDatabase with specified role and fleet_id."""    

    with engine.connect() as con:
        con.execute(text("SET statement_timeout = 10000;"))
        con.execute(text(f"SET ROLE {user};"))
        con.execute(text(f"SET app.fleet_id = '{fleet_id}';"))
        con.commit()  

    database = SQLDatabase(engine)
    return database
