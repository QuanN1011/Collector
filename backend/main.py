from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.buildings import router as buildings_router, single_router as building_single_router
from routes.prospects import router as prospects_router

app = FastAPI(
    title="RainUSE Nexus API",
    description="Hackathon prospecting engine: buildings, rainwater potential, savings proxy, viability score.",
    version="0.1.0",
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
