"""Application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.errors import AppError
from app.database import init_db
from app.services.simulator import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    if os.getenv("SIM_AUTOSTART", "1") == "1":
        engine.ensure_background()
    yield
    engine.shutdown()


app = FastAPI(
    title="Smart Machine Monitoring Dashboard",
    description=(
        "Local software simulation of a factory machine-monitoring system. "
        "The API does not connect to PLCs, SCADA, or physical equipment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.exception_handler(AppError)
async def app_error_handler(_request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "message": "Smart Machine Monitoring API",
        "docs": "/docs",
        "health": "/api/health",
    }
