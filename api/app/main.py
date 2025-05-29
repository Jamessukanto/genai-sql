import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db import database
from app.services.sql_service.sql_service import sql_router
from app.services.chat_service.chat_service import chat_router
from app.services.auth_service.auth_service import auth_router


app = FastAPI()
app.include_router(sql_router)
app.include_router(chat_router)
app.include_router(auth_router)

@app.on_event("startup")
async def on_startup():
    await database.connect()

@app.on_event("shutdown")
async def on_shutdown():
    await database.disconnect()

@app.get("/ping")
async def ping():
    return {"status": "ok"}


# Serve minimal frontend 
fe_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../frontend")
)
if os.path.isdir(fe_path):
    app.mount("/", StaticFiles(directory=fe_path, html=True), name="frontend")
else:
    print("Warning: 'frontend' dir {fe_path} not found.")




