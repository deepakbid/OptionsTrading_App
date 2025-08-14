"""
Main FastAPI application for the Options Strategy Web App.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

from .db import init_db
from .routers import strategies, accounts, runs, connection, changes

app = FastAPI(
    title="Options Trading App",
    description="A comprehensive trading strategy management system",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(connection.router, tags=["connection"])
app.include_router(changes.router, tags=["changes"])

# Templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    """Initialize database and connection manager on startup."""
    await init_db()
    
    # Start the connection manager
    from .connection_manager import connection_manager
    await connection_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    from .connection_manager import connection_manager
    await connection_manager.stop()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the React application."""
    return FileResponse("static/simple.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
