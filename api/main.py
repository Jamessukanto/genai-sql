import os
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db import database
from services.sql_service import sql_router
from services.chat_service import chat_router
from services.auth_service import generate_jwt_token

app = FastAPI()
app.include_router(sql_router)
app.include_router(chat_router)


class ChatRequest(BaseModel):
    query: str
    fleet_id: int

class TokenRequest(BaseModel):
    sub: str
    fleet_id: int


@app.on_event("startup")
async def on_startup():
    await database.connect()

@app.on_event("shutdown")
async def on_shutdown():
    await database.disconnect()

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/generate_jwt_token")
async def generate_jwt_token_endpoint(req: TokenRequest):
    token = generate_jwt_token(req.sub, req.fleet_id)
    return {"token": token}


# Serve minimal frontend 
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print("Warning: 'frontend' directory not found. Static files will not be served.")




