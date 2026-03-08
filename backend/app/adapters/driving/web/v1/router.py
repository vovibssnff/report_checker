from __future__ import annotations

from fastapi import APIRouter

from app.adapters.driving.web.v1 import auth, checks, documents, rules, stats

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(checks.router)
api_router.include_router(rules.router)
api_router.include_router(stats.router)
