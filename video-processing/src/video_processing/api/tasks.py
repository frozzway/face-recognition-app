from fastapi import (
    APIRouter,
    UploadFile,
    Depends,
    Request,
    status
)

from video_processing.services import TaskService
from video_processing.models import TaskStatus


router = APIRouter()


@router.post('/upload')
async def upload_and_process_video(
    video: UploadFile,
    request: Request,
    task_service: TaskService = Depends(),
):
    task_id = await task_service.save_and_process_video(video)
    return {"task_id": task_id, "status_url": request.url_for("get_task_status", task_id=task_id)}


@router.post(
    '/cancel/{task_id}',
    status_code=status.HTTP_200_OK
)
async def cancel_task(
    task_id: str,
    task_service: TaskService = Depends(),
):
    await task_service.cancel_task(task_id)


@router.get(
    '/status/{task_id}',
    response_model=TaskStatus
)
async def get_task_status(
    task_id: str,
    task_service: TaskService = Depends(),
):
    return await task_service.get_task_status(task_id)


@router.get(
    '/status',
    response_model=list[TaskStatus]
)
async def get_tasks_statuses(
    task_service: TaskService = Depends(),
):
    return await task_service.get_tasks_statuses()

