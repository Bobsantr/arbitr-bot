import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq
from dotenv import load_dotenv

from prompt import SYSTEM_PROMPT
from texts import START_TEXT, HELP_TEXT, ABOUT_TEXT
from config import TRIGGER_WORDS

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)


async def get_arbitr_response(user_question: str, context: str = "") -> str:
    try:
        if context:
            full_prompt = (
                f"Контекст (предыдущее сообщение):\n{context}\n\n"
                f"Вопрос пользователя:\n{user_question}"
            )
        else:
            full_prompt = user_question

        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        return "Произошла ошибка при обращении к модели. Попробуй позже."


def should_respond(message: types.Message, bot_username: str) -> bool:
    if not message.text:
        return False

    text = message.text.lower().strip()

    # Вызов через @username
    if f"@{bot_username.lower()}" in text:
        return True

    # Вызов через слова из списка TRIGGER_WORDS
    for word in TRIGGER_WORDS:
        if text.startswith(word):
            return True

    # Ответ на сообщение бота
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot.id:
            return True

    # В личных сообщениях отвечаем всегда
    if message.chat.type == "private":
        return True

    return False


def clean_question(text: str, bot_username: str) -> str:
    """Убирает упоминания бота и триггерные слова из начала сообщения"""
    if not text:
        return ""

    result = text.replace(f"@{bot_username}", "").replace(f"@{bot_username.lower()}", "")
    result = result.strip()

    lower_result = result.lower()
    for word in TRIGGER_WORDS:
        if lower_result.startswith(word):
            result = result[len(word):].strip()
            break

    return result


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(START_TEXT)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(HELP_TEXT)


@dp.message(Command("about"))
async def cmd_about(message: types.Message):
    await message.answer(ABOUT_TEXT)


@dp.message()
async def handle_message(message: types.Message):
    me = await bot.get_me()
    bot_username = me.username

    if not should_respond(message, bot_username):
        return

    question = clean_question(message.text or "", bot_username)

    if not question:
        await message.reply("Напиши, пожалуйста, вопрос.")
        return

    # Сбор контекста
    context = ""
    if message.reply_to_message and message.reply_to_message.text:
        context = message.reply_to_message.text.strip()

    await message.chat.do("typing")

    answer = await get_arbitr_response(question, context)
    await message.reply(answer, parse_mode="Markdown")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())