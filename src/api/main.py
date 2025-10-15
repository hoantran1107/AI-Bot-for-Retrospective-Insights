"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import health, metrics, reports, tasks
from src.core.config import get_settings
from src.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup: Create database tables
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    yield

    # Shutdown: Cleanup if needed
    pass


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    settings = get_settings()

    app = FastAPI(
        title="Retrospective Insights API",
        description=(
            "AI-powered system for analyzing team metrics and generating "
            "actionable retrospective insights with evidence-backed hypotheses "
            "and experiment suggestions."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(reports.router)
    app.include_router(tasks.router)

    return app


# Create app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Retrospective Insights API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
