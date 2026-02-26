import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

user_data = {}

# /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Bot faol ishlamoqda")

# /yaratish
@dp.message(Command("yaratish"))
async def yaratish(message: Message):
    user_data[message.chat.id] = {}
    await message.answer("Nomini yuboring (masalan: Naruto)")

# 1-qadam: nom
@dp.message(F.text & (lambda m: m.chat.id in user_data and "name" not in user_data[m.chat.id]))
async def get_name(message: Message):
    user_data[message.chat.id]["name"] = message.text
    await message.answer("Nechta qism yuboray? (masalan: 100)")

# 2-qadam: miqdor
@dp.message(F.text & (lambda m: m.chat.id in user_data and "count" not in user_data[m.chat.id]))
async def get_count(message: Message):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting!")
    user_data[message.chat.id]["count"] = int(message.text)
    await message.answer("Kanal nomini yuboring (masalan: @AniManxwa)")

# 3-qadam: kanal
@dp.message(F.text & (lambda m: m.chat.id in user_data and "channel" not in user_data[m.chat.id]))
async def get_channel(message: Message):
    user_data[message.chat.id]["channel"] = message.text
    await message.answer("Yuborishni boshladim...")

    name = user_data[message.chat.id]["name"]
    count = user_data[message.chat.id]["count"]
    channel = user_data[message.chat.id]["channel"]

    for i in range(1, count + 1):
        text = f"<b>{name} [<i>{i}-qism</i>] {channel}</b>"
        await message.answer(text)

    await message.answer("Tayyor!")
    del user_data[message.chat.id]

# Oddiy xabarlarni e'tiborsiz qoldirish
@dp.message()
async def ignore(message: Message):
    pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
