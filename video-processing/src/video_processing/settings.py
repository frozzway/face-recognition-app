from pydantic_settings import BaseSettings
from celery import Celery
from miniopy_async import Minio as MinioAsync
from minio import Minio


class Settings(BaseSettings):
    server_host: str = '0.0.0.0'
    server_port: int = '8000'
    redis_address: str = '192.168.0.139'
    redis_port: str = '6380'
    redis_db: str = '3'
    timezone: str = 'Asia/Yekaterinburg'

    minio_access_key: str = 'myminioadmin'
    minio_secret_key: str = 'minio-secret-key-change-me'
    minio_address: str = '192.168.0.139:9000'

    profile_service_address: str = '127.0.0.1:8080'


settings = Settings(
    _env_file='../.env',
    _env_file_encoding='utf-8',
)

redis_full_url = f'redis://{settings.redis_address}:{settings.redis_port}/{settings.redis_db}'

celery = Celery(
    'video_processing',
    broker=redis_full_url,
    backend=redis_full_url,
    include=['video_processing.services'],
    config_source={
        'task_track_started': True,
        'broker_pool_limit': 10,
        'broker_connection_retry_on_startup': True
    }
)

minio_params = {
    "endpoint": settings.minio_address,
    "access_key": settings.minio_access_key,
    "secret_key": settings.minio_secret_key,
    "secure": False
}

async_client = MinioAsync(**minio_params)  # Minio клиент для FastAPI
client = Minio(**minio_params)  # Minio клиент для Celery
