# Face recognition app
☑ **[face-recognition](https://github.com/ageitgey/face_recognition)** для детектирования лиц.<br>
☑ **OpenCV** для прогона по кадрам.<br>
☑ **MinIO** для хранения файлов.<br>
☑ Контейнеризация **docker** и композиция **docker-compose** (не для продакшена: без nginx, изоляции docker network ...).<br>

Оба сервиса написаны на **FastAPI**, соответственно спецификация OpenAPI доступна по адресу `/docs`.

## video-processing (port 50001)
- ✅ **Celery** и **Redis** для фоновой обработки видео (все ядра процессора по умолч.)
- ✅ Асинхронный. **[miniopy-async](https://github.com/hlf20010508/miniopy-async)**, **[aioredis](https://pypi.org/project/aioredis/)**

Сервис отвечает за получение видеофайла от пользователя и отправку задач в очередь на обработку. Можно смотреть статус задачи, можно прекращать выполнение.
Не делает ничего, кроме выявления уникальных лиц на видео, подсчета их количества и отправки их в сервис *profiles-app* для последующей обработки.

## profiles-app (port 56667)
- ✅ Валидирует метаданные профилей с **pydantic**
- ✅ 100мс - запрос на получение 100 профилей (по 5 видео на профиль)
- ✅ Без конфликтов при конкуретности: создании профилей от одновремено обработанных видео.

У каждого профиля/человека - список видео, на которых был запечатлен. Для каждого видео один кроп изображения лица -> (*1 профиль : 3 видео = 3 кропа*)<br>
Можно смотреть отдельные профили, список профилей по выбранному видео, весь список профилей.

![Диаграмма последовательности, надеюсь github не сломает ссылку](https://i.imgur.com/6H7oVJI.png)

## Развертывание
#### Через python скрипт: `deploy.py`
```
python3 deploy.py
```
Или вручную: выполнить 5 команд из директории с клонированным репозиторием
```
sudo docker image build -t python-3-9-dlib-facerecognition -f "Dockerfile-dlib" .
```

```
cd profiles-app && sudo docker image build -t service44_profiles-app .
```

```
cd ../video-processing && sudo docker image build -t service44_video-processing .
```

```
cd .. && sudo docker compose run --rm profiles-app sh -c \
"cd /app/src/migrations && PYTHONPATH=/app/src python update.py"
```

```
sudo docker compose up --detach --force-recreate
```
Готово!
#### *Принять ко вниманию*
> На основе `python-3-9-dlib-facerecognition` строятся *profiles-app* и *video-processing*, поскольку оба сервиса используют `face-recognition`, который в свою очередь зависим от `dlib`. <br>
Dlib строится из исходников, затем с помощью pip устанавливается face-recognition и dlib.<br>
❗ Может занять продолжительное время (±15 минут на 3х выделенных ядрах без AVX) и потребует ~ 2.5 GB свободной памяти
