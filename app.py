from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
from dotenv import load_dotenv
from g4f.client import Client 

# Загружаем переменные из .env
load_dotenv()

# Инициализация FastAPI
app = FastAPI()

# Получаем параметры для Telegram из переменных окружения
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_str = os.getenv("SESSION_STR")

# Инициализация клиента Telethon
client = TelegramClient(StringSession(session_str), api_id, api_hash)


# Модель данных для запроса
class ParseRequest(BaseModel):
    channel_username: str
    posts_count: int
    base_prompt: str


# Функция для получения постов из канала Telegram
async def get_tg_posts(channel_username, posts_count):
    async with client:
        posts = []
        async for message in client.iter_messages(channel_username, limit=posts_count):
            post = f"""Данные за: {message.date.strftime("%Y-%m-%d")}
                sender_id: {message.sender_id}
                текст сообщения: {message.text}
            """
            posts.append(post)
    return posts


# Генерация текста согласно промпту
def process_prompt(prompt):
    # Создаем новый event loop, если текущий уже используется
    # loop = asyncio.get_event_loop()
    # if loop.is_running():
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
        
    client1 = Client()

    response = client1.chat.completions.create(
        # model="gpt-4o-mini", 
        model="gpt-4",
        messages=[
            {
                "role": "user", 
                "content": prompt
                }
            ],
    # Add any other necessary parameters
    )
    return response.choices[0].message.content


# Преобразование в структурированные данные
def get_structured_data(raw_data):
    result = []
    for line in raw_data.split("\n"):
        parts = line.split("===")
        if len(parts) == 5:
            result.append({
                "brand": parts[0].strip(),
                "name": parts[1].strip(),
                "price": parts[2].strip(),
                "date": parts[3].strip(),
                "stock": parts[4].strip(),
                "currency": parts[5].strip()
            })
    return result


# Основная функция для парсинга
async def parse_tg_channel(channel_username, posts_count, base_prompt):
    # Получаем посты из Telegram
    posts = await get_tg_posts(channel_username, posts_count)
    posts_str = "<Start_of_message>. ".join(posts)
    
    # Генерируем ответ с использованием AI
    ai_response = process_prompt(f"{base_prompt} {posts_str}")
    
    # Структурируем данные
    parsed_data = get_structured_data(ai_response)
    
    # Возвращаем результат
    return {
        'posts': posts_str,
        'ai_response': ai_response,
        'parsed_data': parsed_data
    }


# Маршрут для парсинга
@app.post("/parse-tg-channel")
async def parse_channel(request: ParseRequest):
    try:
        # Парсим данные
        result = await parse_tg_channel(request.channel_username, request.posts_count, request.base_prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Стартовое сообщение
@app.get("/")
async def hello_world():
    return {"message": "Hello from FastAPI and Telethon!"}

# Запуск приложения через Uvicorn
# uvicorn app:app --reload
