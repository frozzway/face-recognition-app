import datetime
import secrets
import json
import asyncio

from aioredis import Redis
from celery.app.control import Inspect
from celery.result import AsyncResult
from fastapi import Depends
from fastapi import (
    UploadFile,
    HTTPException,
    status
)

from video_processing.models import TaskStatusFromQueue, TaskStatusFromInspect, TaskStatusFromAsyncResult, TaskStatus
from video_processing.settings import async_client, settings, celery
from .celery_tasks import process_video


async def get_redis_connection():
    con = Redis(
            host=settings.redis_address,
            port=settings.redis_port,
            db=settings.redis_db
        )
    return con


class TaskService:
    def __init__(self, redis_connection=Depends(get_redis_connection)):
        self.redis_connection = redis_connection

    async def save_and_process_video(self, video: UploadFile) -> str:
        if video.content_type != 'video/mp4':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        filename = await self.save_video(video)
        task: AsyncResult = process_video.delay(filename)
        return task.id

    async def save_video(self, video: UploadFile) -> str:
        if video.content_type != 'video/mp4':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        now = datetime.datetime.utcnow()
        suffix = now.strftime("%Y-%m-%d-%H-%M-%S")
        filename = f'{video.filename}-{suffix}-{secrets.token_hex(2)}.mp4'
        await async_client.put_object('videos', filename, video.file, length=video.size)
        return filename

    async def cancel_task(self, task_id: str):
        task: AsyncResult = celery.AsyncResult(task_id)
        task.revoke(terminate=True)

    async def get_task_status(self, task_id: str) -> TaskStatus:
        task: AsyncResult = celery.AsyncResult(task_id)
        return TaskStatusFromAsyncResult(task)

    async def get_tasks_statuses(self) -> list[TaskStatus]:
        inspect: Inspect = celery.control.inspect()
        tasks: list[TaskStatus] = []

        # SUCCESS & PROGRESS & REVOKED tasks
        running_tasks_rows = await self.redis_connection.keys(pattern='celery-task-meta*')
        running_tasks = [celery.AsyncResult(i[17:]) for i in running_tasks_rows]
        tasks.extend([TaskStatusFromAsyncResult(t) for t in running_tasks])

        # PENDING tasks
        queued_tasks_rows = await self.redis_connection.lrange('celery', 0, -1)
        queued_tasks: list[dict] = [json.loads(t.decode()) for t in queued_tasks_rows]
        tasks.extend([TaskStatusFromQueue(t) for t in queued_tasks])

        # RESERVED tasks
        response = await asyncio.to_thread(inspect.reserved)
        if response:
            reserved_tasks: list[dict] = tuple(response.values())[0]
            tasks.extend([TaskStatusFromInspect(t, 'RESERVED') for t in reserved_tasks])

        return tasks
