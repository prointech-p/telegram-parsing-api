from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
from dotenv import load_dotenv
from g4f.client import Client 
import g4f
from pprint import pprint
from openai import OpenAI


# Загружаем переменные из .env
load_dotenv()


# Инициализация FastAPI
app = FastAPI()

# Получаем параметры для Telegram из переменных окружения
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_str = os.getenv("SESSION_STR")
openai_api_key=os.environ.get("OPENAI_API_KEY")

# Инициализация клиента Telethon
client = TelegramClient(StringSession(session_str), api_id, api_hash)


# Модель данных для запроса
class ParseRequest(BaseModel):
    channel_username: str
    posts_count: int
    base_prompt: str
    ai_model: str


# Функция для получения постов из канала Telegram
async def get_tg_posts(channel_username, posts_count):
    async with client:
        posts = []
        async for message in client.iter_messages(channel_username, limit=posts_count):
            post = f"""Данные за: {message.date.strftime("%Y-%m-%d")}
                sender_id: {message.sender_id}
                текст сообщения: {message.text}
            """
            posts.append({"text": post, "date": message.date.strftime("%Y-%m-%d")})
    return posts


# Генерация текста согласно промпту
def process_prompt(prompt, ai_model):
    # Создаем новый event loop, если текущий уже используется
    # loop = asyncio.get_event_loop()
    # if loop.is_running():
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
   
    client1 = Client()

    response = client1.chat.completions.create(
        # model="gpt-4o-mini",
        model="gpt-4",
        # provider=g4f.Provider.Copilot,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
            ],
        stream=True
    )

    full_response = ""

    for chunk in response:
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content  # Добавляем каждый кусок к переменной

    # return response.choices[0].message.content
    return full_response


# Генерация текста согласно промпту
def process_prompt_openai(prompt, ai_model="gpt-4o-mini"):
   
    client1 = OpenAI(api_key=openai_api_key)


    response = client1.chat.completions.create(
        model=ai_model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.choices[0].message.content


# Преобразование в структурированные данные
def get_structured_data(raw_data, data_date):
    result = []
    for line in raw_data.split("\n"):
        parts = line.split("===")
        if len(parts) == 5:
            price = parts[2].strip().replace(".", ",").replace(" ", "")
            result.append({
                "brand": parts[0].strip(),
                "name": parts[1].strip(),
                "price": price,
                "date": data_date,
                "stock": parts[3].strip(),
                "currency": parts[4].strip()
            })
    return result


# Основная функция для парсинга каждого поста отдельно
async def parse_tg_channel_scminer(channel_username, posts_count, base_prompt, ai_model):
    print('SCMiner')
    # client1 = Client()
    # Получаем посты из Telegram
    posts = await get_tg_posts(channel_username, posts_count)
    result = []
    for post in posts:
        post_lines = post["text"].splitlines()
        data_date = post["date"]
        sub_posts = []

        cities = ["Moscow", "Shenzhen", "Hongkong"]

        n = 0
        start_pos = 0
        for i in range(0, len(post_lines)):
            n += 1
            for city in cities:
                if (city in (post_lines[i]) and n > 10) or (i == len(post_lines) - 1):
                    data_sub_str = "\n".join(post_lines[start_pos:i]) 
                    sub_posts.append(data_sub_str)
                    start_pos = i
        
        ai_response = ""
        for item in sub_posts:
            response_text = process_prompt(base_prompt + ' ' + item, ai_model)
            # response = client1.chat.completions.create(
            #     model="gpt-4",
            #     # provider=g4f.Provider.Copilot,
            #     messages=[
            #         {
            #             "role": "user",
            #             # "role": "assistant",
            #             "content": base_prompt + ' ' + item
            #         }
            #         ]
            # )

            # ai_response = ai_response + response.choices[0].message.content
            ai_response = ai_response + response_text

        # Структурируем данные
        parsed_data = get_structured_data(ai_response, data_date)

        result.insert(
            0, 
            {
                'post': post["text"],
                'ai_response': ai_response,
                'parsed_data': parsed_data
            }
        )
    
    # Возвращаем результат
    return result


# Основная функция для парсинга каждого поста отдельно
async def parse_tg_channel_detail(channel_username, posts_count, base_prompt, ai_model="gpt-4", alg='g4f'):
    # Получаем посты из Telegram
    posts = await get_tg_posts(channel_username, posts_count)
    result = ["test"]
    for post in posts:
        post_str = "<Start_of_post>. " + post["text"]

        if alg == 'openai':
            ai_response = process_prompt_openai(f"{base_prompt} {post_str}")
        else:
             ai_response = process_prompt(f"{base_prompt} {post_str}", ai_model)

    #     # Структурируем данные
        parsed_data = get_structured_data(ai_response, post["date"])

        result.append({
            'post': post_str,
            'ai_response': ai_response,
            'parsed_data': parsed_data
        })
    
    # Возвращаем результат
    return result


# Основная функция для парсинга каждого поста отдельно ПО ЧАСТЯМ
# async def parse_tg_channel_by_parts(channel_username, posts_count, base_prompt, ai_model):
#     # Получаем посты из Telegram
#     posts = await get_tg_posts(channel_username, posts_count)
#     result = []
#     for post in posts:
#         post_str = "<Start_of_post>. " + post["text"]

#         parts = post_str.split("\n\n")  # Разделяем по двойным переводам строки
       
#         ai_response = ""
#         for part in parts:
#             # Генерируем ответ с использованием AI
#             ai_response = ai_response + "\nNEW_PART\n" + process_prompt(f"{base_prompt} {part}", ai_model)
        
#         # Структурируем данные
#         parsed_data = get_structured_data(ai_response)

#         result.append({
#             'post': post_str,
#             'ai_response': ai_response,
#             'parsed_data': parsed_data
#         })
    
#     # Возвращаем результат
#     return result


# Основная функция для парсинга всех постов вместе
# async def parse_tg_channel(channel_username, posts_count, base_prompt):
#     # Получаем посты из Telegram
#     posts = await get_tg_posts(channel_username, posts_count)
#     posts_str = "<Start_of_message>. ".join(posts)
    
#     # Генерируем ответ с использованием AI
#     ai_response = process_prompt(f"{base_prompt} {posts_str}")
    
#     # Структурируем данные
#     parsed_data = get_structured_data(ai_response)
    
#     # Возвращаем результат
#     return {
#         'posts': posts_str,
#         'ai_response': ai_response,
#         'parsed_data': parsed_data
#     }


# Маршрут для парсинга
# @app.post("/parse-tg-channel")
# async def parse_channel(request: ParseRequest):
#     try:
#         # Парсим данные
#         result = await parse_tg_channel(request.channel_username, request.posts_count, request.base_prompt)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# Маршрут для парсинга
@app.post("/parse-tg-channel-detail")
async def parse_channel(request: ParseRequest):
    try:
        # Парсим данные
        if request.channel_username == "@ASICMINERether77":
            result = await parse_tg_channel_scminer(
                channel_username=request.channel_username, 
                posts_count=request.posts_count, 
                base_prompt=request.base_prompt, 
                ai_model=request.ai_model)
        else:
            result = await parse_tg_channel_detail(
                channel_username=request.channel_username, 
                posts_count=request.posts_count, 
                base_prompt=request.base_prompt, 
                ai_model=request.ai_model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Маршрут для парсинга
@app.post("/parse-tg-channel-openai")
async def parse_channel(request: ParseRequest):
    try:
        # Парсим данные
        result = await parse_tg_channel_detail(
            channel_username=request.channel_username, 
            posts_count=request.posts_count, 
            base_prompt=request.base_prompt, 
            ai_model="gpt-4o-mini",
            alg='openai')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Маршрут для парсинга
# @app.post("/parse-tg-channel-by-parts")
# async def parse_channel(request: ParseRequest):
#     try:
#         # Парсим данные
#         result = await parse_tg_channel_by_parts(request.channel_username, request.posts_count, request.base_prompt, request.ai_model)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# Стартовое сообщение
@app.get("/")
async def hello_world():
    return {"message": "Hello from FastAPI and Telethon!"}

# Запуск приложения через Uvicorn
# uvicorn app:app --reload

