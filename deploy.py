import subprocess

commands = [
    "sudo docker image build -t python-3-9-dlib-facerecognition -f \"Dockerfile-dlib\" .",
    "sudo docker image build -t service44_profiles-app .",
    "sudo docker image build -t service44_video-processing .",
    "sudo docker compose run --rm profiles-app sh -c \"cd /app/src/migrations && PYTHONPATH=/app/src python update.py\"",
    "sudo docker compose up --detach --force-recreate"
]

directories = [
    ".",
    "profiles-app",
    "video-processing",
    ".",
    "."
]

try:
    for command, directory in zip(commands, directories):
        print(f"Выполняю команду: {command}\n")
        subprocess.run(command, shell=True, check=True, cwd=directory)
        print()
except subprocess.CalledProcessError as e:
    print(f"Команда {e.cmd} завершилась с ошибкой: {e.returncode}")
    exit(1)

print("Скрипт завершен")