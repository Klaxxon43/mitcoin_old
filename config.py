import os
# Задаем переменные окружения
API_TOKEN = os.environ["API_TOKEN"]
CRYPTOBOT_TOKEN = os.environ["CRYPTOBOT_TOKEN"]
HOST='0.0.0.0'
PORT=8000
BASE_URL='' #можно через ngrok
WEBHOOK_PATH = f'/{API_TOKEN}'

ADMINS_ID = [996459546, 2118524898, 6806012624]
