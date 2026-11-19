"""Aggregate all API routers."""

from fastapi import APIRouter

from src.presentation.api.routes import auth, blogs, health, uploads, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(blogs.router)
api_router.include_router(health.router)
api_router.include_router(uploads.router)
api_router.include_router(users.router)
