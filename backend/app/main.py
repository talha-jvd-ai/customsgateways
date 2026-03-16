from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from app.api.pipeline_routes import router as pipeline_router
from app.api.classification_routes import router as classification_router
from app.database import init_database, test_connection as test_db
from app.services.qdrant_service import init_collections, test_connection as test_qdrant
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("=" * 60)
    print("  CustomsGateways Pipeline API")
    print("=" * 60)

    # Create directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.results_dir, exist_ok=True)

    # Test connections
    db_ok = test_db()
    qdrant_ok = test_qdrant()

    if db_ok:
        print("✅ PostgreSQL connected")
        init_database()
    else:
        print("❌ PostgreSQL connection failed")

    if qdrant_ok:
        print("✅ Qdrant connected")
        init_collections()
    else:
        print("⚠️  Qdrant not available — classification will not work")

    print("=" * 60)
    print("  Startup complete — API ready")
    print("=" * 60)

    yield

    print("Shutting down...")


app = FastAPI(
    title="CustomsGateways Pipeline API",
    description="AI-powered customs data optimization pipeline",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline routes (new)
app.include_router(pipeline_router, prefix="/api/v1", tags=["pipeline"])

# Classification routes (existing, preserved)
app.include_router(classification_router, prefix="/api/v1", tags=["classification"])


@app.get("/")
async def root():
    return {
        "service": "CustomsGateways Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "pipeline": {
            "upload": "POST /api/v1/pipeline/upload",
            "execute": "POST /api/v1/pipeline/execute",
            "status": "GET /api/v1/pipeline/status/{run_id}",
            "download": "GET /api/v1/pipeline/download/{run_id}/{step_id}",
            "analytics": "GET /api/v1/pipeline/analytics/{run_id}",
        }
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
