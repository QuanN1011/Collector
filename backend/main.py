from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text

from env_load import load_backend_env

load_backend_env()

from fastapi.middleware.cors import CORSMiddleware

from api_key.dependencies import require_api_key
from api_key.routes_issue import router as api_keys_issue_router
from database.config import get_database_url
from database.engine import get_engine, init_db
from routes.analyze_building import router as analyze_building_router
from routes.buildings import router as buildings_router, single_router as building_single_router
from routes.prospects import router as prospects_router
from routes.states import router as states_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables when DATABASE_URL points at Postgres (+ PostGIS extension)."""
    if get_database_url():
        init_db()
    yield


app = FastAPI(
    title="RainUSE Nexus API",
    description="Hackathon prospecting engine: buildings, rainwater potential, savings proxy, viability score.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(states_router, dependencies=[Depends(require_api_key)])
app.include_router(buildings_router, dependencies=[Depends(require_api_key)])
app.include_router(building_single_router, dependencies=[Depends(require_api_key)])
app.include_router(prospects_router, dependencies=[Depends(require_api_key)])
app.include_router(analyze_building_router, dependencies=[Depends(require_api_key)])
app.include_router(api_keys_issue_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    """PostgreSQL connectivity (no API key)."""
    if not get_database_url():
        return {"status": "ok", "database": "not_configured"}
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
