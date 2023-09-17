from fastapi import FastAPI
from fastapi.routing import APIRoute
from . import api
from .settings import client


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


def create_bucket(name: str):
    if not client.bucket_exists(name):
        client.make_bucket(name)


create_bucket('videos')
create_bucket('face-crops')

app = FastAPI()

app.include_router(api.router)
use_route_names_as_operation_ids(app)
