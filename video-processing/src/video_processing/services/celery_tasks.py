import pickle
import secrets
import tempfile
from base64 import urlsafe_b64encode
from io import BytesIO
from pathlib import Path

import cv2
import face_recognition
import requests

from video_processing.settings import client, celery, settings


@celery.task(bind=True)
def process_video(self, filename: str):
    meta = {
        "progress": 'unknown',
        "known_faces": 0,
        "video": filename
    }
    # Не нашел способа создать объект VideoCapture из файла, хранящегося в памяти, поэтому загружаю в Temp и выгружаю из
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name)
    client.fget_object('videos', filename, file_path=temp_path / filename)
    video = cv2.VideoCapture(str(temp_path / filename))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    known_faces = []
    for i in range(total_frames):
        ret, frame = video.read()
        if not ret:
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        for face_num, face_encoding in enumerate(face_encodings):
            known_faces_encodings = [encoding for encoding, _ in known_faces]
            match = face_recognition.compare_faces(known_faces_encodings, face_encoding, tolerance=0.50)
            if not any(match):
                face_location = face_locations[face_num]
                face = get_face(face_location, frame, face_encoding)
                known_faces.append(face)
        progress = (i + 1) / total_frames * 100
        meta = {
            "progress": str(progress),
            "known_faces": len(known_faces),
            "video": filename
        }
        self.update_state(state="PROGRESS", meta=meta)
    video.release()
    temp_dir.cleanup()

    request_data = {
        "video_filename": filename,
        "processed_data": []
    }

    for encoding, face_filename in known_faces:
        dumped = pickle.dumps(encoding)
        base64_encoded = urlsafe_b64encode(dumped).decode()
        item = {
            'encoding': base64_encoded,
            'crop_filename': face_filename
        }
        request_data['processed_data'].append(item)

    # call service 2
    url = f'http://{settings.profile_service_address}/profiles'
    requests.post(url, json=request_data, timeout=10)

    return meta


def get_face(face_location, frame, face_encoding):
    # Получить кроп изображения лица
    top, right, bottom, left = face_location
    face_crop = frame[top:bottom, left:right]
    face_image_filename = f'{secrets.token_urlsafe(32)}.jpg'
    base64_encoded = cv2.imencode('.jpg', face_crop)[1]
    readable = BytesIO(base64_encoded)
    # Сохранить кроп в бакете
    client.put_object('face-crops', face_image_filename, readable, length=len(base64_encoded))
    # Добавить лицо в коллекцию найденных лиц
    item = (face_encoding, face_image_filename)
    return item