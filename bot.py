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
user_states = {}
user_combo_data = {}


def process_textcopy_message(text):
    """
    /textcopy uchun matnni qayta ishlash
    HTML kodlarni qo'llab-quvvatlaydi
    """
    results = []
    
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\s*-\s*(\d+)\}'
    text_pattern = r'\{(\d+)\s*-\s*text\s*-\s*(\d+)\}'
    textenter_pattern = r'\{(\d+)\s*-\s*textenter\s*-\s*(\d+)\}'
    
    # {0 - raqam - 1} - alohida xabarlar (HTML parse qilinadi)
    for match in re.finditer(raqam_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        for i in range(start, start + count):
            msg = template.format(i)
            results.append(("individual", msg, 'HTML'))
    
    # {0 - text - 1} - bitta xabarda (HTML parse qilinadi)
    for match in re.finditer(text_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        parts = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", ", ".join(parts), 'HTML'))
    
    # {0 - textenter - 1} - yangi qatordan (HTML parse qilinadi)
    for match in re.finditer(textenter_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        lines = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", "\n".join(lines), 'HTML'))
    
    return results


def process_combo_format(text):
    """
    /combo format matnni qayta ishlash
    """
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\}'
    text_raqam_pattern = r'\{(\d+)\s*-\s*text\s*raqam\}'
    
    has_raqam = bool(re.search(raqam_pattern, text))
    has_text_raqam = bool(re.search(text_raqam_pattern, text))
    
    return has_raqam or has_text_raqam


def get_combo_format_type(text):
    """
    Combo format turini aniqlash
    """
    raqam_pattern = r'\{(\d+)\s*-\s*raqam\}'
    text_raqam_pattern = r'\{(\d+)\s*-\s*text\s*raqam\}'
    
    if re.search(raqam_pattern, text):
        match = re.search(raqam_pattern, text)
        return 'raqam', int(match.group(1)), match.group(0)
    elif re.search(text_raqam_pattern, text):
        match = re.search(text_raqam_pattern, text)
        return 'text_raqam', int(match.group(1)), match.group(0)
    
    return None, 0, ""


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
        "   Masalan: <code>&lt;b&gt;Darslik {1 - raqam - 15}&lt;/b&gt;</code>\n"
        "   <i>HTML kodlar ishlaydi!</i>\n\n"
        "2️⃣ <code>{0 - text - 1}</code> - Bitta xabarda yonma-yon\n"
        "   Masalan: <code>&lt;i&gt;Salom {1 - text - 20}&lt;/i&gt;</code>\n\n"
        "3️⃣ <code>{0 - textenter - 1}</code> - Yangi qatordan\n"
        "   Masalan: <code>&lt;b&gt;salom {1 - textenter - 4}&lt;/b&gt;</code>\n\n"
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
        "📝 <b>2 xil format mavjud:</b>\n\n"
        "1️⃣ <code>{1 - raqam}</code> - <b>HTML kodlar ishlaydi</b>\n"
        "   Masalan: <code>&lt;b&gt;Video {1 - raqam}&lt;/b&gt;</code>\n"
        "   Natija: <b>Video 1</b>, <b>Video 2</b>, ...\n\n"
        "2️⃣ <code>{1 - text raqam}</code> - <b>Oddiy text</b>\n"
        "   Masalan: <code>&lt;i&gt;Video {1 - text raqam}&lt;/i&gt;</code>\n"
        "   Natija: &lt;i&gt;Video 1&lt;/i&gt; (oddiy text)\n\n"
        "📎 <b>Ishlash tartibi:</b>\n"
        "1️⃣ Formatni yuboring\n"
        "2️⃣ Video/rasm/fayllarni yuboring\n"
        "3️⃣ /stop buyrug'i bilan yakunlang\n\n"
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
        
        format_type, start_num, pattern_text = get_combo_format_type(format_text)
        
        bot.reply_to(
            message, 
            f"✅ <b>{len(files)} ta fayl qabul qilindi. Nomlash boshlandi...</b>", 
            parse_mode='HTML'
        )
        
        for idx, file_info in enumerate(files):
            number = start_num + idx
            caption = format_text.replace(pattern_text, str(number))
            
            # Format turiga qarab parse_mode tanlash
            if format_type == 'raqam':
                # HTML kodlar ishlaydi
                parse = 'HTML'
            else:
                # Oddiy text
                parse = None
            
            try:
                if file_info['type'] == 'video':
                    bot.send_video(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
                elif file_info['type'] == 'photo':
                    bot.send_photo(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
                elif file_info['type'] == 'document':
                    bot.send_document(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
                elif file_info['type'] == 'audio':
                    bot.send_audio(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
            except Exception as e:
                # Agar HTML xatosi bo'lsa, oddiy text sifatida yuborish
                bot.send_video(message.chat.id, file_info['file_id'], caption=caption, parse_mode=None)
            
            time.sleep(0.1)
        
        bot.send_message(message.chat.id, "✅ <b>Barcha fayllar nomlandi!</b>", parse_mode='HTML')
        
        # Ma'lumotlarni tozalash
        user_states[user_id] = None
        if user_id in user_combo_data:
            del user_combo_data[user_id]
    
    else:
        bot.reply_to(message, "❌ Siz /combo rejimida emassiz yoki hali format kiritmadingiz!")


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id, None)
    
    # /textcopy rejimi - HTML parse qilish bilan
    if state == 'textcopy':
        if any(pattern in text for pattern in ['- raqam -', '- text -', '- textenter -']):
            try:
                results = process_textcopy_message(text)
                for msg_type, msg_content, parse_mode in results:
                    if msg_type == "individual":
                        try:
                            bot.send_message(message.chat.id, msg_content, parse_mode=parse_mode)
                        except:
                            bot.send_message(message.chat.id, msg_content, parse_mode=None)
                        time.sleep(0.05)
                    else:
                        try:
                            bot.send_message(message.chat.id, msg_content, parse_mode=parse_mode)
                        except:
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
            bot.reply_to(
                message, 
                "✅ Format qabul qilindi!\n\n"
                "📎 Endi video/rasm/fayllarni yuboring.\n"
                "/stop buyrug'i bilan yakunlang."
            )
        else:
            bot.reply_to(
                message, 
                "❌ Format xato! Iltimos, {1 - raqam} yoki {1 - text raqam} formatidan foydalaning.\n\n"
                "Masalan:\n"
                "<b>Video {1 - raqam}</b> - HTML ishlaydi\n"
                "Video {1 - text raqam} - oddiy text",
                parse_mode='HTML'
            )
    
    elif state == 'combo_files':
        bot.reply_to(message, "📎 Iltimos, video/rasm/fayl yuboring yoki /stop buyrug'i bilan yakunlang.")
    else:
        bot.reply_to(message, "Iltimos, avval /textcopy yoki /combo buyrug'ini yuboring.")


@bot.message_handler(content_types=['video', 'photo', 'document', 'audio'])
def handle_files(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, None)
    
    if state == 'combo_files' and user_id in user_combo_data:
        file_info = {}
        
        if message.video:
            file_info = {'type': 'video', 'file_id': message.video.file_id}
        elif message.photo:
            file_info = {'type': 'photo', 'file_id': message.photo[-1].file_id}
        elif message.document:
            file_info = {'type': 'document', 'file_id': message.document.file_id}
        elif message.audio:
            file_info = {'type': 'audio', 'file_id': message.audio.file_id}
        
        user_combo_data[user_id]['files'].append(file_info)
        files_count = len(user_combo_data[user_id]['files'])
        
        bot.reply_to(
            message, 
            f"✅ Fayl qabul qilindi! (Jami: {files_count} ta)\n"
            "/stop buyrug'i bilan yakunlang."
        )
    
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
