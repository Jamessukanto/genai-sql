import os
from typing import Dict, Any, Tuple
# from langchain.chat_models import init_chat_model  # [MISTRAL] Commented out for Groq
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

from core.db_con import engine
from core.llm_agent.agent import build_agent
from core.llm_agent.utils import get_model_config, MODELS
from routes.chat.utils import create_session_aware_database

# Add Groq import
from langchain_groq import ChatGroq

# Global cache for fleet-based agent instances and their databases
_fleet_agent_cache: Dict[str, Tuple[Any, SQLDatabase]] = {}

async def get_or_create_agent_for_fleet(fleet_id: str, user: str, model_name: str = "mistral-medium-latest"):
    """
    Get cached agent for fleet or create new one, with fresh fleet context applied.
    """
    cache_key = f"fleet_{fleet_id}:{user}:{model_name}"
    print(f"[AGENT MANAGER] Agent cache key: {cache_key}")
    
    if cache_key not in _fleet_agent_cache:
        print(f"[AGENT MANAGER] Creating new agent: {cache_key}")
        
        # Create fresh model and database
        from core.llm_agent.utils import MODELS
        model_config = get_model_config(model_name)
        # Accept both key and value for llama3-70b
        llama3_keys = ["llama3-70b", MODELS["llama3-70b"]]

        if model_name in llama3_keys:
            # --- GROQ/Llama 3.3 70B path ---
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model=model_config["model"],
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
                api_key=os.getenv("GROQ_API_KEY")
            )
        else:
            # Use MISTRAL 
            # llm = init_chat_model(**model_config)
            llm = None  # Set to None for clarity

        # Create a session-aware database with proper session variable enforcement
        db = create_session_aware_database(user, fleet_id)

        agent = await build_agent(db, llm)
        _fleet_agent_cache[cache_key] = agent
    else:
        print(f"[AGENT MANAGER] Using cached agent: {cache_key}")
    
    return _fleet_agent_cache[cache_key]

def clear_agent_cache(fleet_id: str = None, user: str = None):
    """
    Clear agent cache for specific fleet/user or all.
    
    Args:
        fleet_id: Specific fleet to clear, or None to clear all
        user: Specific user to clear, or None to clear all
    """
    if fleet_id is None and user is None:
        _fleet_agent_cache.clear()
        print("Cleared all fleet agent cache")
    elif fleet_id is not None and user is None:
        keys_to_remove = [key for key in _fleet_agent_cache.keys() if key.startswith(f"{fleet_id}:")]
        for key in keys_to_remove:
            del _fleet_agent_cache[key]
        print(f"Cleared agent cache for fleet {fleet_id}")
    elif fleet_id is not None and user is not None:
        keys_to_remove = [key for key in _fleet_agent_cache.keys() if key.startswith(f"{fleet_id}:{user}:")]
        for key in keys_to_remove:
            del _fleet_agent_cache[key]
        print(f"Cleared agent cache for fleet {fleet_id}, user {user}")

def get_agent_cache_stats():
    """
    Get statistics about the agent cache.
    
    Returns:
        Dict with cache statistics
    """
    return {
        "total_cached_agents": len(_fleet_agent_cache),
        "cache_keys": list(_fleet_agent_cache.keys())
    } 