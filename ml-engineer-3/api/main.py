"""ParkSight ML-platform API — feedback loop, review, retraining.

Run:  uvicorn api.main:app --reload --port 8001
Docs: http://localhost:8001/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers import feedback, forecast, retraining, review
from common.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="ParkSight ML Platform API", version="0.3.0", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(feedback.router)
app.include_router(review.router)
app.include_router(retraining.router)
app.include_router(forecast.router)
