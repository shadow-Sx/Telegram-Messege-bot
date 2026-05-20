import os
import re
import time
import telebot
from flask import Flask, request

# Flask server yaratish (Render uchun kerak)
app = Flask(__name__)

# Environment variable'dan tokenni olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)

# Foydalanuvchi holatini saqlash
user_states = {}


def process_textcopy_message(text):
    """Matnni qayta ishlash - /textcopy uchun"""
    results = []
    
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\s*-\s*(\d+)\}'
    text_pattern = r'\{(\d+)\s*-\s*text\s*-\s*(\d+)\}'
    textenter_pattern = r'\{(\d+)\s*-\s*textenter\s*-\s*(\d+)\}'
    
    # {0 - raqam - 1} - alohida xabarlar
    for match in re.finditer(raqam_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        for i in range(start, start + count):
            msg = template.format(i)
            results.append(("individual", msg))
    
    # {0 - text - 1} - bitta xabarda vergul bilan
    for match in re.finditer(text_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        parts = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", ", ".join(parts)))
    
    # {0 - textenter - 1} - yangi qatordan
    for match in re.finditer(textenter_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        lines = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", "\n".join(lines)))
    
    return results


def process_combo_message(text):
    """Matnni qayta ishlash - /combo uchun"""
    result = text
    
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\s*-\s*(\d+)\}'
    text_raqam_pattern = r'\{(\d+)\s*-\s*text\s*raqam\s*-\s*(\d+)\}'
    
    # {0 - raqam - 1}
    for match in re.finditer(raqam_pattern, result):
        start = int(match.group(1))
        count = int(match.group(2))
        numbers = [str(i) for i in range(start, start + count)]
        result = result.replace(match.group(0), ", ".join(numbers), 1)
    
    # {0 - text raqam - 1}
    for match in re.finditer(text_raqam_pattern, result):
        start = int(match.group(1))
        count = int(match.group(2))
        numbers = [str(i) for i in range(start, start + count)]
        result = result.replace(match.group(0), ", ".join(numbers), 1)
    
    return result


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 <b>Salom! Men TextCopy Bot man</b>\n\n"
        "Men sizga matnlarni nusxalash va raqamlashda yordam beraman.\n\n"
        "📋 <b>Mavjud buyruqlar:</b>\n"
        "• /textcopy - Matn nusxalash\n"
        "• /combo - Kombinatsiyalash\n\n"
        "Har bir buyruq haqida batafsil ma'lumot olish uchun buyruqni yuboring."
    )
    bot.reply_to(message, welcome_text, parse_mode='HTML')


@bot.message_handler(commands=['textcopy'])
def cmd_textcopy(message):
    user_id = message.from_user.id
    user_states[user_id] = 'textcopy'
    
    help_text = (
        "📝 <b>TextCopy buyrug'i uchun formatlar:</b>\n\n"
        "1️⃣ <code>{0 - raqam - 1}</code> - Alohida xabarlarda raqamlash\n"
        "   Masalan: <code>Raqamlash nomlari {137 - raqam - 50}-Raqami</code>\n"
        "   137 dan 187 gacha 50 ta alohida xabar yuboradi\n\n"
        "2️⃣ <code>{0 - text - 1}</code> - Bitta xabarda yonma-yon\n"
        "   Masalan: <code>Salom {1 - text - 20}</code>\n"
        "   Natija: Salom 1, Salom 2, ..., Salom 20\n\n"
        "3️⃣ <code>{0 - textenter - 1}</code> - Yangi qatordan\n"
        "   Masalan: <code>salom {1 - textenter - 4}</code>\n"
        "   Natija:\n"
        "   salom 1\n"
        "   salom 2\n"
        "   salom 3\n"
        "   salom 4\n\n"
        "✍️ <b>Endi kerakli formatda matn yuboring!</b>"
    )
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(commands=['combo'])
def cmd_combo(message):
    user_id = message.from_user.id
    user_states[user_id] = 'combo'
    
    help_text = (
        "🔄 <b>Combo buyrug'i uchun formatlar:</b>\n\n"
        "1️⃣ <code>{0 - raqam - 1}</code> - Raqamlarni avtomatik qo'shish\n"
        "   Masalan: <code>Raqamlar: {1 - raqam - 5}</code>\n"
        "   Natija: Raqamlar: 1, 2, 3, 4, 5\n\n"
        "2️⃣ <code>{0 - text raqam - 1}</code> - Textni raqamlab qo'shish\n"
        "   Masalan: <code>Sonlar: {10 - text raqam - 5}</code>\n"
        "   Natija: Sonlar: 10, 11, 12, 13, 14\n\n"
        "✍️ <b>Endi kerakli formatda matn yuboring!</b>"
    )
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id, None)
    
    if state == 'textcopy':
        if any(pattern in text for pattern in ['- raqam -', '- text -', '- textenter -']):
            results = process_textcopy_message(text)
            for msg_type, msg_content in results:
                if msg_type == "individual":
                    bot.send_message(message.chat.id, msg_content)
                    time.sleep(0.05)
                else:
                    bot.send_message(message.chat.id, msg_content)
        else:
            bot.reply_to(message, "❌ Format xato! Iltimos, to'g'ri formatdan foydalaning.")
    
    elif state == 'combo':
        if any(pattern in text for pattern in ['- raqam -', '- text raqam -']):
            result = process_combo_message(text)
            bot.send_message(message.chat.id, result)
        else:
            bot.reply_to(message, "❌ Format xato! Iltimos, to'g'ri formatdan foydalaning.")
    
    else:
        bot.reply_to(message, "Iltimos, avval /textcopy yoki /combo buyrug'ini yuboring.")


# Flask route - Render Web Service uchun
@app.route('/')
def index():
    return "Bot is running!"


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'error', 403


if __name__ == '__main__':
    # Webhook o'rnatish yoki polling
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    if WEBHOOK_URL:
        # Webhook orqali ishlash
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
    else:
        # Polling orqali ishlash
        print("Bot polling mode da ishga tushdi...")
        bot.infinity_polling()
