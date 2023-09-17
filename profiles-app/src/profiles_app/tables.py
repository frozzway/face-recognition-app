from sqlalchemy import (
    Column, String, Integer, LargeBinary,
    ForeignKey, Date, Enum
)

from sqlalchemy.ext.declarative import declarative_base

from profiles_app.models import Sex


Base = declarative_base()


class UserProfile(Base):
    __tablename__ = 'user_profile'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    middlename = Column(String, nullable=True)
    sex = Column(Enum(Sex), nullable=True)
    birth_date = Column(Date, nullable=True)

    encoding = Column(LargeBinary)

    def __hash__(self):
        return hash(self.id)


class VideoData(Base):
    __tablename__ = 'video_data'

    profile_id = Column(Integer, ForeignKey('user_profile.id', ondelete="CASCADE"), primary_key=True)
    video_filename = Column(String, primary_key=True)
    crop_filename = Column(String)

