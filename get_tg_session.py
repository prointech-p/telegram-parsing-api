from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

API_ID = os.environ.get('API_ID', '123456')
API_HASH = os.environ.get('API_HASH', 'HASH123456')

# print(f"API_ID: {API_ID}")
# print(f"API_HASH: {API_HASH}")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("Ваша session строка:")
    print(client.session.save())  # Сохраните эту строку!