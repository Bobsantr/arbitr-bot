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

    if f"@{bot_username.lower()}" in text:
        return True

    if text.startswith("арбитр") or text.startswith("!арбитр"):
        return True

    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot.id:
            return True

    if message.chat.type == "private":
        return True

    return False


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я независимый арбитр.\n\n"
        "Вызови меня командой /help, чтобы узнать, как пользоваться."
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "Как пользоваться ботом:\n\n"
        "• Напиши «Арбитр» и свой вопрос\n"
        "• Или упомяни @ArbitrTGBot\n"
        "• Можно ответить на любое сообщение и написать «Арбитр» — я учту его как контекст\n\n"
        "Примеры:\n"
        "Арбитр кто правее в этом споре?\n"
        "Арбитр объясни, в чём разница между этими позициями\n\n"
        "Я могу:\n"
        "— разбирать споры\n"
        "— оценивать силу аргументов\n"
        "— давать пояснения по теме"
    )
    await message.answer(text)


@dp.message(Command("about"))
async def cmd_about(message: types.Message):
    text = (
        "Я — независимый арбитр для споров в Telegram.\n\n"
        "• Работаю без прав администратора\n"
        "• Вижу только те сообщения, в которых меня вызвали\n"
        "• Не принадлежу владельцу канала и не подстраиваюсь под него\n"
        "• Стараюсь отделять факты от мнений и не занимать сторону автоматически\n\n"
        "Если спор ценностный — прямо говорю об этом.\n"
        "Если одна позиция сильнее по фактам — тоже говорю прямо."
    )
    await message.answer(text)


@dp.message()
async def handle_message(message: types.Message):
    me = await bot.get_me()
    bot_username = me.username

    if not should_respond(message, bot_username):
        return

    question = message.text or ""

    # Убираем упоминания бота
    question = question.replace(f"@{bot_username}", "")
    question = question.replace(f"@{bot_username.lower()}", "")

    if question.lower().startswith("арбитр"):
        question = question[6:].strip()
    elif question.lower().startswith("!арбитр"):
        question = question[7:].strip()

    question = question.strip()

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
