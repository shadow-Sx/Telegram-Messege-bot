import logging
import os
from aiogram import Bot, Dispatcher, executor, types

# Logging
logging.basicConfig(level=logging.INFO)

# Tokenni Railway Variables dan olamiz
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Railway Variables ga qo‘shing.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# /start komandasi
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Salom! Bot ishlayapti 🚀")


# Oddiy echo
@dp.message_handler()
async def echo_handler(message: types.Message):
    await message.answer(f"Siz yozdingiz: {message.text}")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
