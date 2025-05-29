from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase

from db import engine
from app.llm.agent import build_agent
from app.services.service_utils import get_user_info
from app.services.chat_service.chat_service_utils import (
    apply_session_variables_with_engine,
    apply_session_variables_with_sql_database,
)


chat_router = APIRouter(prefix="/chat")

class ChatRequest(BaseModel):
    query: str


@chat_router.post("/execute_user_query")
async def execute_user_query(req: ChatRequest, user_info: dict = Depends(get_user_info)):
    """
    Processes a user’s natural language query using an LLM agent configured per user and fleet.
    
    NOTE: This LLM agent setup runs per-request for demo flexibility (dynamic fleet_id via UI).
          In production, to be moved to user session to avoid re-initialization.
    """
    print("\n\n" + ("="*80) + "\nExecuting user query.\n")

    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    # Set up LLM agent
    try:
        llm = init_chat_model(model="mistral-medium-latest", temperature=0)
        apply_session_variables_with_engine(engine, user, fleet_id)
        db = SQLDatabase(engine=engine)
        apply_session_variables_with_sql_database(db, user, fleet_id)
        agent = await build_agent(db, llm)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to set up LLM agent: {e}"
        )
    
    # Run LLM agent
    try:
        messages = [{"role": "user", "content": req.query}]
        steps = []
        for step in agent.stream({"messages": messages}, stream_mode="values"):
            step["messages"][-1].pretty_print()
            steps.append(step)
            print()

        final_response = steps[-1]["messages"][-1].content
        return {"response": final_response}
    
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to run LLM agent: {e}"
        )
    







   
