"""Top-level API router aggregating all feature routers under /api."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import baselines, ears, items, links, projects, regression, reviews

api_router = APIRouter(prefix="/api")
api_router.include_router(projects.router)
api_router.include_router(items.router)
api_router.include_router(links.router)
api_router.include_router(reviews.router)
api_router.include_router(baselines.router)
api_router.include_router(ears.router)
api_router.include_router(regression.router)
