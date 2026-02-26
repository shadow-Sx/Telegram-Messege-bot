import os
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot faol ishlamoqda")

@bot.message_handler(commands=['yaratish'])
def yaratish(message):
    user_data[message.chat.id] = {}
    bot.reply_to(message, "Nomini yuboring (masalan: Naruto)")

@bot.message_handler(func=lambda m: m.chat.id in user_data and "name" not in user_data[m.chat.id])
def get_name(message):
    user_data[message.chat.id]["name"] = message.text
    bot.reply_to(message, "Nechta qism yuboray? (masalan: 100)")

@bot.message_handler(func=lambda m: m.chat.id in user_data and "count" not in user_data[m.chat.id])
def get_count(message):
    if not message.text.isdigit():
        return bot.reply_to(message, "Faqat raqam kiriting!")
    user_data[message.chat.id]["count"] = int(message.text)
    bot.reply_to(message, "Kanal nomini yuboring (masalan: @AniManxwa)")

@bot.message_handler(func=lambda m: m.chat.id in user_data and "channel" not in user_data[m.chat.id])
def get_channel(message):
    user_data[message.chat.id]["channel"] = message.text
    bot.reply_to(message, "Yuborishni boshladim...")

    name = user_data[message.chat.id]["name"]
    count = user_data[message.chat.id]["count"]
    channel = user_data[message.chat.id]["channel"]

    for i in range(1, count + 1):
        text = f"<b>{name} [<i>{i}-qism</i>] {channel}</b>"
        bot.send_message(message.chat.id, text)

    bot.send_message(message.chat.id, "Tayyor!")
    del user_data[message.chat.id]

@bot.message_handler(func=lambda m: True)
def ignore(message):
    pass

bot.polling()
