import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from groq import Groq
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

# Системный промпт арбитра
SYSTEM_PROMPT = """Ты — независимый и непредвзятый арбитр в спорах.

Твои принципы:
- Максимальная нейтральность
- Отделяй факты от мнений
- Оценивай силу аргументов, а не симпатии
- Говори спокойно, ясно и по делу
- Не пытайся мирить любой ценой
- Если одна сторона аргументирована сильнее — прямо так и скажи
- Если спор ценностный и нет объективной правоты — укажи на это

Отвечай структурировано и достаточно кратко."""

async def get_arbitr_response(user_question: str) -> str:
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",  # хорошая модель на Groq
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question}
            ],
            temperature=0.3,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        return "Произошла ошибка при обращении к модели. Попробуй позже."

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я независимый арбитр.\n\n"
        "Просто упомяни меня (@ArbitrTGBot) и задай вопрос по спору, "
        "или ответь на моё сообщение."
    )

@dp.message()
async def handle_message(message: types.Message):
    # Проверяем, что бота упомянули или ответили на его сообщение
    bot_mentioned = False
    if message.text and f"@{ (await bot.get_me()).username }" in message.text:
        bot_mentioned = True
    if message.reply_to_message and message.reply_to_message.from_user.id == (await bot.me()).id:
        bot_mentioned = True

    if not bot_mentioned and message.chat.type != "private":
        return  # игнорируем обычные сообщения в группах

    question = message.text or ""
    if not question.strip():
        await message.reply("Напиши, пожалуйста, вопрос.")
        return

    # Убираем упоминание бота из текста
    bot_username = (await bot.get_me()).username
    question = question.replace(f"@{bot_username}", "").strip()

    await message.chat.do("typing")  # статус "печатает"

    answer = await get_arbitr_response(question)
    await message.reply(answer)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
