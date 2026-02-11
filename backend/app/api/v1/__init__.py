"""
API v1 router aggregator.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import documents, validation, reports, search

api_router = APIRouter()

api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(validation.router, prefix="/validation", tags=["Validation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
