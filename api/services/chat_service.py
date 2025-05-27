from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import database
from services.auth_service import get_user_info 
from llm.agent import agent

chat_router = APIRouter(prefix="/chat")

class ChatRequest(BaseModel):
    query: str


@chat_router.post("/execute_user_query")
async def chat(req: ChatRequest, user_info: dict = Depends(get_user_info)):
    print("Executing user query.\n")
    user = user_info["user"]
    fleet_id = user_info["fleet_id"]

    try:
        # Set up timeout and role-based authorization with RLS
        async with database.connection() as con:
            await con.execute("SET statement_timeout = 10000;")
            await con.execute(f"SET ROLE {user};")
            await con.execute(f"SET app.fleet_id = '{fleet_id}';")

        # Stream agent response
        steps = []
        messages = [{"role": "user", "content": req.query}]
        for step in agent.stream({"messages": messages}, stream_mode="values"):
            print()
            step["messages"][-1].pretty_print()
            steps.append(step)

        final_response = steps[-1]["messages"][-1].content
        print("\nFinal response:", final_response)
        return {"response": final_response}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

