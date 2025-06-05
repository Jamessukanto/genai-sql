from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

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
    """Asynchronous function that establishes a connection to the database on startup.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        HTTPException: If the database connection fails, with a 500 status code and an error message.
    """
    try:
        await database.connect()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to database: {e}"
        )   

@app.on_event("shutdown")
async def on_shutdown():
    """Asynchronously handles the shutdown process by disconnecting from the database.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        HTTPException: If there is an error disconnecting from the database.
    """
    try:
        await database.disconnect()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to disconnect from database: {e}"
        )

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}


# @app.get("/")
# async def root():
#     """Redirect root path to /app"""
#     return RedirectResponse(url="/app")

# # Serve minimal frontend under /app path
# fe_path = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "../frontend")
# )
# if os.path.isdir(fe_path):
#     app.mount("/app", StaticFiles(directory=fe_path, html=True), name="frontend")
# else:
#     print(f"Warning: 'frontend' dir {fe_path} not found.")




