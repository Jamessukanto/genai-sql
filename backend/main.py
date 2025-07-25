from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.db_con import database
from routes.sql.sql import sql_router
from routes.chat.chat import chat_router
from routes.auth.auth import auth_router


app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes under /api prefix
app.include_router(sql_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    """Asynchronous function that establishes a connection to the database on startup."""
    try:
        await database.connect()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to database: {e}"
        )   

@app.on_event("shutdown")
async def on_shutdown():
    """Asynchronously handles the shutdown process by disconnecting from the database."""
    try:
        await database.disconnect()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to disconnect from database: {e}"
        )

@app.get("/")
async def root():
    return {"message": "GenAI SQL Backend API", "status": "running"}

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}

