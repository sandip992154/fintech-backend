"""
Member Management Router Module
Combines all member-related routes in a clean, modular structure
"""
from fastapi import APIRouter

from services.routers.member_core_routes import router as core_router
from services.routers.member_admin_routes import router as admin_router

# Create main member router
router = APIRouter()

# Include sub-routers
router.include_router(core_router, tags=["Members - Core"])
router.include_router(admin_router, tags=["Members - Admin"])

# Export for use in main.py
__all__ = ["router"]