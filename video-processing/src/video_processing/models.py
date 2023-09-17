import base64
import json

from pydantic import BaseModel
from celery.result import AsyncResult


class TaskStatus(BaseModel):
    status: str
    task_id: str
    progress: str = '0'
    known_faces: int = 0
    video: str


class TaskStatusFromAsyncResult:
    def __new__(cls, task: AsyncResult):
        has_started = isinstance(task.info, dict)
        args = {
            "status": task.status,
            "task_id": task.id,
            "progress": f"{task.info.get('progress', '0%')}%" if has_started else '0%',
            "known_faces": task.info.get('known_faces', 0) if has_started else 0,
            "video": task.info.get('video', 'unavailable') if has_started else ''
        }
        return TaskStatus(**args)

class TaskStatusFromQueue:
    def __new__(cls, task: dict):
        body = base64.b64decode(task['body']).decode()
        video_filename = json.loads(body)[0][0]
        args = {
            "status": 'PENDING',
            "task_id": task['headers']['id'],
            "video": video_filename
        }
        return TaskStatus(**args)


class TaskStatusFromInspect:
    def __new__(cls, task: dict, status: str):
        args = {
            "status": status,
            "task_id": task['id'],
            "video": task['args'][0]
        }
        return TaskStatus(**args)