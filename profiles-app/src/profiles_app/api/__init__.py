from fastapi import APIRouter

from .profiles import router as profile_router

router = APIRouter()

router.include_router(profile_router)