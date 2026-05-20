import os
import re
import time
import threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Foydalanuvchi ma'lumotlarini saqlash
user_states = {}  # Holat: textcopy, combo_format, combo_files
user_combo_data = {}  # /combo uchun: format va fayllar ro'yxati


def process_textcopy_message(text):
    """Matnni qayta ishlash - /textcopy uchun"""
    results = []
    
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\s*-\s*(\d+)\}'
    text_pattern = r'\{(\d+)\s*-\s*text\s*-\s*(\d+)\}'
    textenter_pattern = r'\{(\d+)\s*-\s*textenter\s*-\s*(\d+)\}'
    
    for match in re.finditer(raqam_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        for i in range(start, start + count):
            results.append(("individual", template.format(i)))
    
    for match in re.finditer(text_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        parts = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", ", ".join(parts)))
    
    for match in re.finditer(textenter_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        lines = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", "\n".join(lines)))
    
    return results


def process_combo_format(text):
    """Combo format matnni qayta ishlash"""
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\s*-\s*(\d+)\}'
    text_raqam_pattern = r'\{(\d+)\s*-\s*text\s*raqam\s*-\s*(\d+)\}'
    
    # Formatlarni tekshirish
    has_raqam = bool(re.search(raqam_pattern, text))
    has_text_raqam = bool(re.search(text_raqam_pattern, text))
    
    return has_raqam or has_text_raqam


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 <b>Salom! Men TextCopy Bot man</b>\n\n"
        "Men sizga matnlarni nusxalash va raqamlashda yordam beraman.\n\n"
        "📋 <b>Mavjud buyruqlar:</b>\n"
        "• /textcopy - Matn nusxalash va raqamlash\n"
        "• /combo - Fayllarni nomlash\n\n"
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
    user_states[user_id] = 'combo_format'
    
    help_text = (
        "🔄 <b>Combo buyrug'i - Fayllarni nomlash</b>\n\n"
        "Bu buyruq orqali siz yuborgan video/rasm/fayllarni avtomatik nomlab beraman.\n\n"
        "📝 <b>Ishlash tartibi:</b>\n"
        "1️⃣ Avval formatni yuboring:\n"
        "   Masalan: <code>Mening videom {1 - raqam - 5}</code>\n"
        "   Yoki: <code>Video {1 - text raqam - 5}</code>\n\n"
        "2️⃣ Keyin video/rasm/fayllarni yuboring\n"
        "   (xohlagancha fayl yuborishingiz mumkin)\n\n"
        "3️⃣ /stop buyrug'i bilan yakunlang\n"
        "   Men sizga barcha fayllarni nomlab beraman\n\n"
        "✍️ <b>Avval formatni yuboring:</b>"
    )
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(commands=['stop'])
def cmd_stop(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, None)
    
    if state == 'combo_files' and user_id in user_combo_data:
        combo_data = user_combo_data[user_id]
        format_text = combo_data['format']
        files = combo_data['files']
        
        if not files:
            bot.reply_to(message, "❌ Hech qanday fayl yubormadingiz!")
            return
        
        raqam_pattern = r'\{(\d+)\s*-\s*raqam\s*-\s*(\d+)\}'
        text_raqam_pattern = r'\{(\d+)\s*-\s*text\s*raqam\s*-\s*(\d+)\}'
        
        raqam_match = re.search(raqam_pattern, format_text)
        text_raqam_match = re.search(text_raqam_pattern, format_text)
        
        bot.reply_to(message, f"✅ <b>{len(files)} ta fayl qabul qilindi. Nomlash boshlandi...</b>", parse_mode='HTML')
        
        if raqam_match:
            start = int(raqam_match.group(1))
            count = int(raqam_match.group(2))
            
            # Fayllarni nomlab yuborish
            for idx, file_info in enumerate(files[:count]):
                number = start + idx
                caption = format_text.replace(raqam_match.group(0), str(number))
                
                if file_info['type'] == 'video':
                    bot.send_video(message.chat.id, file_info['file_id'], caption=caption)
                elif file_info['type'] == 'photo':
                    bot.send_photo(message.chat.id, file_info['file_id'], caption=caption)
                elif file_info['type'] == 'document':
                    bot.send_document(message.chat.id, file_info['file_id'], caption=caption)
                elif file_info['type'] == 'audio':
                    bot.send_audio(message.chat.id, file_info['file_id'], caption=caption)
                
                time.sleep(0.1)
        
        elif text_raqam_match:
            start = int(text_raqam_match.group(1))
            count = int(text_raqam_match.group(2))
            
            # Fayllarni nomlab yuborish
            for idx, file_info in enumerate(files[:count]):
                number = start + idx
                caption = format_text.replace(text_raqam_match.group(0), str(number))
                
                if file_info['type'] == 'video':
                    bot.send_video(message.chat.id, file_info['file_id'], caption=caption)
                elif file_info['type'] == 'photo':
                    bot.send_photo(message.chat.id, file_info['file_id'], caption=caption)
                elif file_info['type'] == 'document':
                    bot.send_document(message.chat.id, file_info['file_id'], caption=caption)
                elif file_info['type'] == 'audio':
                    bot.send_audio(message.chat.id, file_info['file_id'], caption=caption)
                
                time.sleep(0.1)
        
        bot.send_message(message.chat.id, "✅ <b>Barcha fayllar nomlandi!</b>", parse_mode='HTML')
        
        # Ma'lumotlarni tozalash
        user_states[user_id] = None
        del user_combo_data[user_id]
    
    else:
        bot.reply_to(message, "❌ Siz /combo rejimida emassiz yoki hali format kiritmadingiz!")


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id, None)
    
    # /textcopy rejimi
    if state == 'textcopy':
        if any(pattern in text for pattern in ['- raqam -', '- text -', '- textenter -']):
            try:
                results = process_textcopy_message(text)
                for msg_type, msg_content in results:
                    if msg_type == "individual":
                        bot.send_message(message.chat.id, msg_content, parse_mode=None)
                        time.sleep(0.05)
                    else:
                        bot.send_message(message.chat.id, msg_content, parse_mode=None)
            except Exception as e:
                bot.reply_to(message, f"❌ Xatolik: {str(e)}")
        else:
            bot.reply_to(message, "❌ Format xato! Iltimos, to'g'ri formatdan foydalaning.")
    
    # /combo rejimi - format kiritish
    elif state == 'combo_format':
        if process_combo_format(text):
            user_states[user_id] = 'combo_files'
            user_combo_data[user_id] = {
                'format': text,
                'files': []
            }
            bot.reply_to(message, "✅ Format qabul qilindi!\n\n📎 Endi video/rasm/fayllarni yuboring.\n/stop buyrug'i bilan yakunlang.")
        else:
            bot.reply_to(message, "❌ Format xato! Iltimos, {0 - raqam - 1} yoki {0 - text raqam - 1} formatidan foydalaning.")
    
    # Boshqa holatlar
    elif state == 'combo_files':
        bot.reply_to(message, "📎 Iltimos, video/rasm/fayl yuboring yoki /stop buyrug'i bilan yakunlang.")
    else:
        bot.reply_to(message, "Iltimos, avval /textcopy yoki /combo buyrug'ini yuboring.")


@bot.message_handler(content_types=['video', 'photo', 'document', 'audio'])
def handle_files(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, None)
    
    if state == 'combo_files' and user_id in user_combo_data:
        # Fayl ma'lumotlarini aniqlash
        file_info = {}
        
        if message.video:
            file_info = {
                'type': 'video',
                'file_id': message.video.file_id
            }
        elif message.photo:
            file_info = {
                'type': 'photo',
                'file_id': message.photo[-1].file_id  # Eng katta rasm
            }
        elif message.document:
            file_info = {
                'type': 'document',
                'file_id': message.document.file_id
            }
        elif message.audio:
            file_info = {
                'type': 'audio',
                'file_id': message.audio.file_id
            }
        
        # Faylni ro'yxatga qo'shish
        user_combo_data[user_id]['files'].append(file_info)
        
        files_count = len(user_combo_data[user_id]['files'])
        bot.reply_to(message, f"✅ Fayl qabul qilindi! (Jami: {files_count} ta)\n/stop buyrug'i bilan yakunlang.")
    
    elif state == 'combo_format':
        bot.reply_to(message, "❌ Avval formatni yuboring!")
    else:
        bot.reply_to(message, "Iltimos, avval /combo buyrug'ini yuboring.")


@app.route('/')
def index():
    return "Bot is running 24/7!"


def run_bot():
    """Botni polling bilan ishga tushirish"""
    print("Bot ishga tushmoqda...")
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)


if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
