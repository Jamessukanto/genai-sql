from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import asyncio
from typing import List, Dict, Any

from core.db_con import engine
from routes.utils import get_user_info
from core.llm_agent.utils import get_timeout
from core.llm_agent.agent_manager import get_or_create_agent_for_fleet, get_agent_cache_stats


chat_router = APIRouter(prefix="/chat")

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] 
    query: str  # For frontend latest query


@chat_router.get("/agent_stats")
async def get_agent_stats():
    """Get agent cache statistics for debugging."""
    return get_agent_cache_stats()


@chat_router.post("/execute_user_query")
async def execute_user_query(req: ChatRequest, user_info: dict = Depends(get_user_info)):
    """
    Processes a user's natural language query using an LLM agent configured per user and fleet.
    """
    print("\n\n" + ("="*80) + "\nExecuting conversational chat query.\n")
    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    # Get cached agent with fresh fleet context
    try:
        agent = await get_or_create_agent_for_fleet(fleet_id, user)

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
    







   
