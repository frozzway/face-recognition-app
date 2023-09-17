import pickle
import base64

import face_recognition
import minio.error
from numpy import ndarray
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import delete, select, insert, text
from sqlalchemy.exc import IntegrityError

from profiles_app.database import get_session, engine
from profiles_app.models import *
from profiles_app.tables import UserProfile, VideoData
from profiles_app.settings import client


class ProfileService:
    def __init__(
        self,
        session: Session = Depends(get_session)
    ):
        self.session = session

    @staticmethod
    def load_encoding(encoding: str) -> ndarray:
        byted = encoding.encode()
        dumped = base64.urlsafe_b64decode(byted)
        return pickle.loads(dumped)

    def upload_profiles(
        self,
        profiles_data: ProfilesUpload
    ):
        with engine.begin() as conn:
            # Лок от конкурентных запросов на upload_profiles. EXCLUSIVE mode является self-conflicting, но
            # не запрещает querying таблицы другими транзакциями (не конфликтует с ACCESS SHARE)
            conn.execute(text('LOCK ONLY user_profile IN EXCLUSIVE MODE'))
            profiles = conn.execute(
                select(UserProfile.id, UserProfile.encoding)
            ).all()

            for uploaded_profile in profiles_data.processed_data:
                face_encoding = self.load_encoding(uploaded_profile.encoding)
                known_faces_encodings = [pickle.loads(p[1]) for p in profiles]
                match = face_recognition.compare_faces(known_faces_encodings, face_encoding, tolerance=0.50)

                if not any(match):
                    profile_id = self._create_profile(face_encoding, conn)
                else:
                    matched_index = next((i for i in range(len(match)) if match[i]))
                    profile_id = profiles[matched_index][0]

                conn.execute(insert(VideoData.__table__).values(
                    profile_id=profile_id,
                    video_filename=profiles_data.video_filename,
                    crop_filename=uploaded_profile.crop_filename
                ))

    def _create_profile(self, encoding: ndarray, conn) -> int:
        arr_bytes = pickle.dumps(encoding)
        result = conn.execute(
            insert(UserProfile.__table__).values(encoding=arr_bytes)
        )
        return result.inserted_primary_key[0]

    def _get_profile(self, profile_id: int) -> UserProfile:
        profile = self.session.query(UserProfile).filter_by(id=profile_id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return profile

    def construct_profile_response(
        self,
        profile_id: int,
        request: Request
    ) -> ProfileResponse:
        profile = self._get_profile(profile_id)
        videos = self.session.query(VideoData).filter(VideoData.profile_id == profile_id).all()
        profile_videos = \
            [ProfileVideo(
                video_link=str(request.url_for('download_video', filename=v.video_filename)),
                crop_link=str(request.url_for('download_crop', filename=v.crop_filename)))
            for v in videos]
        return ProfileResponse(
            profile=profile,
            videos=profile_videos
        )

    def construct_many_profiles_response(self, request: Request) -> list[ProfileResponse]:
        rows = self.session.execute(
            select(VideoData, UserProfile)
            .join(UserProfile)
        ).all()
        profiles = {}
        for r in rows:
            profile = r.UserProfile
            if not profiles.get(profile):
                profiles[profile] = []
            video = ProfileVideo(
                video_link=str(request.url_for('download_video', filename=r.VideoData.video_filename)),
                crop_link=str(request.url_for('download_crop', filename=r.VideoData.crop_filename))
            )
            profiles[profile].append(video)
        return [ProfileResponse(profile=profile, videos=videos) for profile, videos in profiles.items()]

    def construct_video_response(
        self,
        video_filename: str,
        request: Request
    ) -> VideoResponse:
        rows = self.session.execute(
            select(VideoData, UserProfile)
            .join(UserProfile)
            .where(VideoData.video_filename == video_filename)
        ).all()
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        profiles = \
            [VideoProfile(
                profile=r.UserProfile,
                crop_link=str(request.url_for('download_crop', filename=r.VideoData.crop_filename)))
            for r in rows]
        return VideoResponse(
            video_link=str(request.url_for('download_video', filename=video_filename)),
            profiles=profiles
        )

    def update_profile(self, profile_id: int, profile_data: BaseProfile) -> UserProfile:
        profile = self._get_profile(profile_id)
        for field, value in profile_data:
            setattr(profile, field, value)
        self.session.commit()
        return profile

    def delete_profile(self, profile_id: int):
        profile = self._get_profile(profile_id)
        try:
            self.session.execute(delete(UserProfile).where(UserProfile.id == profile_id))
            self.session.commit()
        except IntegrityError:
            raise HTTPException(status.HTTP_409_CONFLICT)

    def download_file(self, bucket_name: str, filename: str, media_type: str):
        try:
            response = client.get_object(bucket_name, filename)
        except minio.error.S3Error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if response.status != status.HTTP_200_OK:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(response.data, headers=headers, media_type=media_type)
