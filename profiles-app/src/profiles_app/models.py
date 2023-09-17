import enum
from dataclasses import dataclass
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field
from typing import Annotated, Any
from datetime import date

from pydantic_core import core_schema as cs


Sex = enum.Enum('sex', ['male', 'female'])


@dataclass
class DateGt:
    date: date

    def __get_pydantic_core_schema__(self, source_type: Any, handler) -> cs.CoreSchema:
        def val(v: date) -> date:
            if isinstance(v, date) and not v > self.date:
                raise ValueError(f'Date should be greater than {self.date}')
            return v
        schema = handler(source_type)
        return cs.no_info_after_validator_function(
            val, schema, serialization=schema.get('serialization')
        )


class BaseProfile(BaseModel):
    name: Optional[str] = Field(max_length=50)
    surname: Optional[str] = Field(max_length=50)
    middlename: Optional[str] = Field(max_length=50)
    sex: Optional[Union[Literal["male", "female"], Sex]]
    birth_date: Annotated[Optional[date], DateGt(date(year=1800, month=1, day=1))]

    class Config:
        from_attributes = True


class Profile(BaseProfile):
    id: int


# [_____
# Получение от сервиса видео-обработки
class Face(BaseModel):
    encoding: str
    crop_filename: str


class ProfilesUpload(BaseModel):
    video_filename: str
    processed_data: list[Face]
# _____]


# [_____
# Запрос профиля -> получаем ссылку на каждое видео и кроп лица с видео
class ProfileVideo(BaseModel):
    video_link: str
    crop_link: str


class ProfileResponse(BaseModel):
    profile: Profile
    videos: list[ProfileVideo]
# _____]


# [_____
# Запрос видео -> получаем ссылку на каждый профиль и кроп лица с видео
class VideoProfile(BaseModel):
    profile: Profile
    crop_link: str


class VideoResponse(BaseModel):
    video_link: str
    profiles: list[VideoProfile]
# _____]

