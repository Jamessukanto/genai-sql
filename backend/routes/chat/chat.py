from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import asyncio
from typing import List, Dict, Any
from datetime import datetime 

from core.db_con import engine
from routes.utils import get_user_info
from core.llm_agent.utils import get_model_config
from core.llm_agent.agent_manager import get_or_create_agent_for_fleet


chat_router = APIRouter(prefix="/chat")

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] 
    query: str  # For frontend latest query


@chat_router.post("/execute_user_query")
async def execute_user_query(req: ChatRequest, user_info: dict = Depends(get_user_info)):
    """
    Processes a user's natural language query using an LLM agent configured per user and fleet.
    """
    print(f"\n\n{'='*60} NEW QUERY {'='*60}\n\n")
    print(f"[TS] {datetime.now()} - Start execute_user_query" ) 
    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    # Get cached agent with fresh fleet context
    agent = await get_or_create_agent_for_fleet(fleet_id, user)

    # Only use the latest user message for the agent, to save time
    if req.messages:
        latest_message = req.messages[-1]
        messages = [latest_message]
    else:
        messages = []

    # Run LLM agent with timeout
    try:
        steps = []
        print(f"[TS] {datetime.now()} - Before agent.stream" )  # TIMESTAMPED LOG
        async with asyncio.timeout(get_model_config()["timeout"]):
            for step in agent.stream({"messages": messages}, stream_mode="values"):
                print(f"[TS] {datetime.now()} - Step received from agent.stream" )  # TIMESTAMPED LOG
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
        print(f"[TS] {datetime.now()} - Returning response to client" )  # TIMESTAMPED LOG
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
    







   
