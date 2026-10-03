"""
upay AI Shield - Main FastAPI Application
AI-Powered Transaction Risk & Scam Intelligence Platform
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from backend.config import settings
from backend.database import init_db
from backend.routes import (
    prediction,
    transactions,
    investigation,
    chat,
    dashboard,
    feedback,
    network,
    cases,
    monitoring,
    customers,
    scam,
    timeline,
    simulation,
    stream
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_db()
    yield


app = FastAPI(
    title="upay AI Shield",
    description="AI-Powered Transaction Risk & Scam Intelligence Platform",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )

# Health Check
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Returns system status, model state, and active database configuration."""
    from backend.services.model_service import model_service
    metadata = model_service.get_metadata()
    return {
        "status": "healthy",
        "service": "upay AI Shield",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "model": {
            "name": metadata.get("model_name"),
            "version": metadata.get("model_version"),
            "algorithm": metadata.get("algorithm")
        },
        "governance": {
            "autonomous_blocking_allowed": False,
            "human_in_the_loop_required": True
        }
    }

# Register API routers under /api/v1
app.include_router(prediction.router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)
app.include_router(investigation.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(feedback.router, prefix=settings.API_V1_PREFIX)
app.include_router(network.router, prefix=settings.API_V1_PREFIX)
app.include_router(cases.router, prefix=settings.API_V1_PREFIX)
app.include_router(monitoring.router, prefix=settings.API_V1_PREFIX)
app.include_router(customers.router, prefix=settings.API_V1_PREFIX)
app.include_router(scam.router, prefix=settings.API_V1_PREFIX)
app.include_router(timeline.router, prefix=settings.API_V1_PREFIX)
app.include_router(simulation.router, prefix=settings.API_V1_PREFIX)
app.include_router(stream.router, prefix=settings.API_V1_PREFIX)

# Mount outputs/ for evaluation chart viewing
if os.path.exists("outputs"):
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Mount frontend/ static files if directory exists
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        index_file = os.path.join("frontend", "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend build in progress. Access /api/v1/health for API status."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
