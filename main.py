import os
import time
import telebot
from flask import Flask, request

# ==========================
#   TOKEN
# ==========================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ==========================
#   FLASK SERVER
# ==========================
app = Flask(__name__)

@app.route('/')
def home():
    return "AniTanjiBot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

# ==========================
#   USER STATE
# ==========================
user_state = {}

# ==========================
#   /start
# ==========================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Assalomu alaykum!\n\nQism generator botiga xush kelibsiz.\nBoshlash uchun /yaratish deb yozing.")

# ==========================
#   /yaratish
# ==========================
@bot.message_handler(commands=['yaratish'])
def yaratish(message):
    user_state[message.chat.id] = {}
    bot.reply_to(message, "📌 Kontent nomini yuboring.\n\nMasalan: Naruto")

# ==========================
#   NOM QABUL QILISH
# ==========================
@bot.message_handler(func=lambda m: m.chat.id in user_state and "name" not in user_state[m.chat.id])
def get_name(message):
    user_state[message.chat.id]["name"] = message.text
    bot.reply_to(message, "📌 Nechta qism yuboray?\n\nMasalan: 100")

# ==========================
#   QISM SONI QABUL QILISH
# ==========================
@bot.message_handler(func=lambda m: m.chat.id in user_state and "count" not in user_state[m.chat.id])
def get_count(message):
    if not message.text.isdigit():
        return bot.reply_to(message, "❗ Faqat raqam kiriting!")

    user_state[message.chat.id]["count"] = int(message.text)
    bot.reply_to(message, "📌 Kanal nomini yuboring.\n\nMasalan: @AniManxwa")

# ==========================
#   KANAL NOMI QABUL QILISH
# ==========================
@bot.message_handler(func=lambda m: m.chat.id in user_state and "channel" not in user_state[m.chat.id])
def get_channel(message):
    user_state[message.chat.id]["channel"] = message.text

    name = user_state[message.chat.id]["name"]
    count = user_state[message.chat.id]["count"]
    channel = user_state[message.chat.id]["channel"]

    bot.send_message(message.chat.id, "⏳ Yuborishni boshladim...")

    # ==========================
    #   XABAR YUBORISH (0.7s delay)
    # ==========================
    for i in range(1, count + 1):
        text = f"<b>{name} [<i>{i}-qism</i>] {channel}</b>"
        bot.send_message(message.chat.id, text)
        time.sleep(0.7)  # Telegram bloklamasligi uchun

    bot.send_message(message.chat.id, "✅ Tayyor! Barcha qismlar yuborildi.")

    del user_state[message.chat.id]

# ==========================
#   RUN SERVER
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
