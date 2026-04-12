from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent / ".env")
from fastapi.middleware.cors import CORSMiddleware

from database.config import get_database_url
from database.engine import init_db
from routes.buildings import router as buildings_router, single_router as building_single_router
from routes.prospects import router as prospects_router


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

app.include_router(buildings_router)
app.include_router(building_single_router)
app.include_router(prospects_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
