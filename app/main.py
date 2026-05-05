"""Punto de entrada de FastAPI para SpiralGeoLog v2."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.upload import router as upload_router

app = FastAPI(
    title="SpiralGeoLog API",
    description="Backend de análisis petrofísico para archivos LAS de PEMEX.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router)


@app.get("/")
def raiz() -> dict[str, str]:
    """Endpoint raíz para validación rápida de servicio."""
    return {"app": "SpiralGeoLog API", "version": "2.0.0"}
