import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import ssl

from db import database, engine
from app.services.sql_service.sql_service import sql_router
from app.services.chat_service.chat_service import chat_router
from app.services.auth_service.auth_service import auth_router


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
    try:
        # Create SSL context that accepts self-signed certs
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Update database SSL context
        database.url = database.url.replace("postgresql://", "postgresql+asyncpg://")
        database._backend.ssl = ssl_context
        
        await database.connect()
        # Test the connection
        async with database.connection() as conn:
            await conn.fetch("SELECT 1")
        print("Database connection established successfully")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    try:
        await database.disconnect()
        print("Database connection closed")
    except Exception as e:
        print(f"Error during shutdown: {e}")

@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Test database connection
        async with database.connection() as conn:
            await conn.fetch("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "details": {
                "database_host": str(engine.url.host),
                "database_name": str(engine.url.database)
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}


# Serve frontend under /app path
fe_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../frontend")
)
if os.path.isdir(fe_path):
    app.mount("/app", StaticFiles(directory=fe_path, html=True), name="frontend")
else:
    print(f"Warning: 'frontend' dir {fe_path} not found.")




