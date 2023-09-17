from pydantic_settings import BaseSettings
from minio import Minio


class Settings(BaseSettings):
    server_host: str = '0.0.0.0'
    server_port: int = '8080'
    redis_address: str = '192.168.0.139'
    redis_port: str = '6380'
    redis_db: str = '3'
    timezone: str = 'Asia/Yekaterinburg'

    minio_access_key: str = 'myminioadmin'
    minio_secret_key: str = 'minio-secret-key-change-me'
    minio_address: str = '192.168.0.139:9000'

    db_dialect: str = 'postgresql'
    db_username: str = 'admin'
    db_password: str = '123'
    db_host: str = 'localhost'
    db_port: str = '5432'
    db_database: str = 'profiles_app'


settings = Settings(
    _env_file='../.env',
    _env_file_encoding='utf-8',
)

redis_full_url = f'redis://{settings.redis_address}:{settings.redis_port}/{settings.redis_db}'

minio_params = {
    "endpoint": settings.minio_address,
    "access_key": settings.minio_access_key,
    "secret_key": settings.minio_secret_key,
    "secure": False
}

client = Minio(**minio_params)
