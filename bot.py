import os
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

user_data = {}

# /start buyrug'i
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Bot faol ishlamoqda")

# /yaratish buyrug'i
@dp.message_handler(commands=['yaratish'])
async def yaratish(message: types.Message):
    user_data[message.chat.id] = {}
    await message.answer("Nomini yuboring (masalan: Naruto)")

# 1-qadam: nom
@dp.message_handler(lambda m: m.chat.id in user_data and "name" not in user_data[m.chat.id])
async def get_name(message: types.Message):
    user_data[message.chat.id]["name"] = message.text
    await message.answer("Nechta qism yuboray? (masalan: 100)")

# 2-qadam: miqdor
@dp.message_handler(lambda m: m.chat.id in user_data and "count" not in user_data[m.chat.id])
async def get_count(message: types.Message):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting!")
    user_data[message.chat.id]["count"] = int(message.text)
    await message.answer("Kanal nomini yuboring (masalan: @AniManxwa)")

# 3-qadam: kanal
@dp.message_handler(lambda m: m.chat.id in user_data and "channel" not in user_data[m.chat.id])
async def get_channel(message: types.Message):
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

# Oddiy xabarlarga javob bermaslik
@dp.message_handler()
async def ignore(message: types.Message):
    pass

if __name__ == "__main__":
    executor.start_polling(dp)
