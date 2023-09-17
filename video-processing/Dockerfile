FROM python-3-9-dlib-facerecognition

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src ./src
CMD ["sleep","3600"]
