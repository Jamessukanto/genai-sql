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
    print("\n\n" + ("="*80) + "\nExecuting user query.\n")
    print("in execute user, user_info:", user_info)

    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    try:
        # Set up LLM
        llm = init_chat_model(model="mistral-medium-latest", temperature=0)

        # Set up sql database and session variables
        print("\n=== Setting up session variables ===")
        try:
            apply_session_variables_with_engine(engine, user, fleet_id)
            db = SQLDatabase(engine=engine)
            apply_session_variables_with_sql_database(db, user, fleet_id)
            print("Session variables applied to SQLDatabase")
            
            # Test if session variables are set
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SHOW ALL")).fetchall()
                print("\nCurrent PostgreSQL session variables:")
                for row in result:
                    if 'app.' in str(row[0]):
                        print(f"{row[0]} = {row[1]}")
        except Exception as sess_err:
            print(f"Session variables error: {str(sess_err)}")
            raise HTTPException(status_code=500, detail=f"Failed to set session variables: {str(sess_err)}")

        # Set up for running LLM agent
        agent = await build_agent(db, llm)
        messages = [{"role": "user", "content": req.query}]

        steps = []
        for step in agent.stream({"messages": messages}, stream_mode="values"):
            print("\n=== Agent Step ===")
            print(f"Step type: {type(step)}")
            print(f"Step content: {step}")
            step["messages"][-1].pretty_print()
            steps.append(step)

        final_response = steps[-1]["messages"][-1].content
        print("\nFinal response:", final_response)
        return {"response": final_response}
    
    except Exception as e:
        print(f"\nError in execute_user_query: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    

