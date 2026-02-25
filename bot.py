import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Render Environment Variables ni tekshiring.")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
