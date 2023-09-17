from fastapi import APIRouter

from .tasks import router as task_router

router = APIRouter()

router.include_router(task_router)