import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq
from dotenv import load_dotenv
from prompt import SYSTEM_PROMPT

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

async def get_arbitr_response(user_question: str) -> str:
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
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

def should_respond(message: types.Message, bot_username: str) -> bool:
    """Проверяет, нужно ли боту отвечать на сообщение"""
    if not message.text:
        return False

    text = message.text.lower().strip()

    # Вызов через @username
    if f"@{bot_username.lower()}" in text:
        return True

    # Вызов через слово "арбитр"
    if text.startswith("арбитр") or text.startswith("!арбитр"):
        return True

    # Ответ на сообщение бота
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot.id:
            return True

    # В личных сообщениях отвечаем всегда
    if message.chat.type == "private":
        return True

    return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я независимый арбитр.\n\n"
        "Вызови меня так:\n"
        "• @ArbitrTGBot вопрос\n"
        "• Арбитр вопрос\n\n"
        "Могу разобрать спор или просто объяснить тему."
    )

@dp.message()
async def handle_message(message: types.Message):
    me = await bot.get_me()
    bot_username = me.username

    if not should_respond(message, bot_username):
        return

    question = message.text or ""
    
    # Убираем упоминания из текста
    question = question.replace(f"@{bot_username}", "")
    question = question.replace(f"@{bot_username.lower()}", "")
    
    if question.lower().startswith("арбитр"):
        question = question[6:].strip()
    if question.lower().startswith("!арбитр"):
        question = question[7:].strip()

    question = question.strip()

    if not question:
        await message.reply("Напиши, пожалуйста, вопрос.")
        return

    await message.chat.do("typing")

    answer = await get_arbitr_response(question)
    await message.reply(answer, parse_mode="Markdown")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
