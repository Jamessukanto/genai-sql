from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from routes.chat.chat import chat_router
from routes.auth.auth import auth_router


app = FastAPI(
    title="GenAI SQL Backend API",
    description="A FastAPI backend for GenAI SQL operations with chat, authentication, and database management",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Chat & AI", 
            "description": "Endpoints for natural language chat interactions with LLM agents"
        },
        {
            "name": "Authentication",
            "description": "JWT token generation and authentication endpoints"
        },
        {
            "name": "Health Check",
            "description": "System health and status endpoints"
        }
    ]
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes under /api prefix
app.include_router(chat_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/", tags=["Health Check"])
async def root():
    """API overview with links to documentation"""
    return {
        "message": "GenAI SQL Backend API",
        "status": "running",
        "version": "1.0.0",
        "documentation": {
            "alternative_docs": "/redoc",
        },
        "endpoints": {
            "health_check": "/api/ping",
            "chat": "/api/chat/*",
            "auth": "/api/auth/*"
        },
        "quick_links": {
            "health_check": "/api/ping"
        }
    }

@app.get("/api/ping", tags=["Health Check"])
async def ping():
    return {"status": "ok"}

