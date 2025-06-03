from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import asyncio
from typing import List, Dict, Any

from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase

from core.db_con import engine
from core.llm_agent.agent import build_agent
from routes.utils import get_user_info
from core.llm_agent.utils import get_model_config, get_timeout, DEFAULT_MODEL
from routes.chat.utils import (
    apply_session_variables_with_engine,
    apply_session_variables_with_sql_database,
)


chat_router = APIRouter(prefix="/chat")

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] 
    query: str  # For frontend latest query


@chat_router.post("/execute_user_query")
async def execute_user_query(req: ChatRequest, user_info: dict = Depends(get_user_info)):
    """
    Processes a user's natural language query using an LLM agent configured per user and fleet.
    
    NOTE: This LLM agent setup runs per-request for demo flexibility (dynamic fleet_id via UI).
          In production, 'init_chat_model' is to be moved to user session to avoid re-initialization.
    """
    print("\n\n" + ("="*80) + "\nExecuting conversational chat query.\n")
    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    # Set up LLM agent
    try:
        model_config = get_model_config()
        llm = init_chat_model(**model_config)

        apply_session_variables_with_engine(engine, user, fleet_id)
        db = SQLDatabase(engine=engine)
        apply_session_variables_with_sql_database(db, user, fleet_id)

        agent = await build_agent(db, llm)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to set up LLM agent: {e}"
        )

    # Run LLM agent with timeout
    try:
        messages = req.messages
        steps = []

        # Add timeout for the entire streaming operation
        async with asyncio.timeout(get_timeout()):
            for step in agent.stream({"messages": messages}, stream_mode="values"):
                step["messages"][-1].pretty_print()
                steps.append(step)
                print()

        if not steps:
            raise HTTPException(
                status_code=500,
                detail="No response generated from LLM agent"
            )

        # Final LLM output (may include intermediate tool call messages)
        final_response = steps[-1]["messages"][-1].content
        return {"response": final_response}

    except asyncio.TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=f"Request timed out while waiting for LLM agent: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to run LLM agent: {e}"
        )
    







   
