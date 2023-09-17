from fastapi import APIRouter, Depends, status, Request

from profiles_app.models import *
from profiles_app.services import ProfileService

router = APIRouter()


@router.post(
    '/profiles',
    status_code=status.HTTP_200_OK
)
def upload_profiles(
    profiles_data: ProfilesUpload,
    profile_service: ProfileService = Depends(),
):
    profile_service.upload_profiles(profiles_data)


@router.get(
    '/profiles/{profile_id}',
    response_model=ProfileResponse
)
def get_profile(
    profile_id: int,
    request: Request,
    profile_service: ProfileService = Depends(),
):
    return profile_service.construct_profile_response(profile_id, request)

@router.get(
    '/profiles',
    response_model=list[ProfileResponse]
)
def get_all_profiles(
    request: Request,
    profile_service: ProfileService = Depends(),
):
    return profile_service.construct_many_profiles_response(request)


@router.put(
    '/profiles/{profile_id}',
    response_model=BaseProfile
)
def update_profile(
    profile_id: int,
    profile_data: BaseProfile,
    profile_service: ProfileService = Depends(),
):
    return profile_service.update_profile(profile_id, profile_data)


@router.get(
    '/video/{video_filename}/profiles',
    response_model=VideoResponse
)
def get_profiles_on_video(
    video_filename: str,
    request: Request,
    profile_service: ProfileService = Depends(),
):
    return profile_service.construct_video_response(video_filename, request)


@router.delete(
    '/profiles/{profile_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_profile(
    profile_id: int,
    profile_service: ProfileService = Depends(),
):
    profile_service.delete_profile(profile_id)


@router.get(
    '/video/{filename}',
)
def download_video(
    filename: str,
    profile_service: ProfileService = Depends(),
):
    return profile_service.download_file('videos', filename, 'video/mp4')

@router.get(
    '/crop/{filename}',
)
def download_crop(
    filename: str,
    profile_service: ProfileService = Depends(),
):
    return profile_service.download_file('face-crops', filename, 'image/jpeg')
