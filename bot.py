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
    ֎ belgisi bilan ishlaydi
    """
    results = []
    
    # Regex naqshlar ֎ belgisi bilan
    raqam_pattern = r'֎(\d+)\s*-\s*raqam\s*-\s*(\d+)֎'
    text_pattern = r'֎(\d+)\s*-\s*text\s*-\s*(\d+)֎'
    textenter_pattern = r'֎(\d+)\s*-\s*textenter\s*-\s*(\d+)֎'
    
    # ֎0 - raqam - 1֎ - alohida xabarlar
    for match in re.finditer(raqam_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        for i in range(start, start + count):
            msg = template.format(i)
            results.append(("individual", msg, 'HTML'))
    
    # ֎0 - text - 1֎ - bitta xabarda
    for match in re.finditer(text_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        parts = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", ", ".join(parts), 'HTML'))
    
    # ֎0 - textenter - 1֎ - yangi qatordan
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
    raqam_pattern = r'֎(\d+)\s*-\s*raqam֎'
    text_raqam_pattern = r'֎(\d+)\s*-\s*text\s*raqam֎'
    
    has_raqam = bool(re.search(raqam_pattern, text))
    has_text_raqam = bool(re.search(text_raqam_pattern, text))
    
    return has_raqam or has_text_raqam


def get_combo_format_type(text):
    """
    Combo format turini aniqlash
    """
    raqam_pattern = r'֎(\d+)\s*-\s*raqam֎'
    text_raqam_pattern = r'֎(\d+)\s*-\s*text\s*raqam֎'
    
    raqam_match = re.search(raqam_pattern, text)
    text_raqam_match = re.search(text_raqam_pattern, text)
    
    if raqam_match:
        return 'raqam', int(raqam_match.group(1)), raqam_match.group(0)
    elif text_raqam_match:
        return 'text_raqam', int(text_raqam_match.group(1)), text_raqam_match.group(0)
    
    return None, 0, ""


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 <b>Salom! Men Avto Nomlash Bot man</b>\n\n"
        "Men sizga matnlarni nusxalash va raqamlashda yordam beraman.\n\n"
        "📋 <b>Mavjud buyruqlar:</b>\n"
        "• /textcopy - Matn nusxalash va raqamlash\n"
        "• /combo - Fayllarni nomlash\n\n"
        "Botdan maroq bilan foydalaning | @AvtoNomlash"
    )
    bot.reply_to(message, welcome_text, parse_mode='HTML')


@bot.message_handler(commands=['textcopy'])
def cmd_textcopy(message):
    user_id = message.from_user.id
    user_states[user_id] = 'textcopy'
    
    help_text = """
Salom menga text yuboring textingiz Ichida <code>֎0 - raqam - 1֎</code>, <code>֎0 - text - 1֎</code>, <code>֎0 - textenter - 1֎</code> bo'lsa men sizga ularni raqamlab yozib beraman

📝 <b>TextCopy buyrug'i uchun qo'llanma:</b>
1️⃣ <code>֎0 - raqam - 1֎</code> - Alohida xabarlarda raqamlash
2️⃣ <code>֎0 - text - 1֎</code> - Bitta xabarda yonma-yon
3️⃣ <code>֎0 - textenter - 1֎</code> - Yangi qatordan

✍️ <b>Endi kerakli formatda matn yuboring!</b>
"""
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(commands=['combo'])
def cmd_combo(message):
    user_id = message.from_user.id
    user_states[user_id] = 'combo_format'
    
    help_text = """
Salom menga <code>֎1 - raqam֎</code>, <code>֎1 - text raqam֎</code> buyruqlardan foydalanib menga habar yuboring men ularni sizning habaringizga qoshib beraman

<code>֎1 - raqam֎</code> - Raqam bilan nomlash
<code>֎1 - text raqam֎</code> - Matn va raqam bilan nomlash

✍️ <b>Yaxshi endi habaringizni yuboring:</b>
    """
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
            user_states[user_id] = None
            if user_id in user_combo_data:
                del user_combo_data[user_id]
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
                parse = 'HTML'
            else:
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
                try:
                    if file_info['type'] == 'video':
                        bot.send_video(message.chat.id, file_info['file_id'], caption=caption, parse_mode=None)
                    elif file_info['type'] == 'photo':
                        bot.send_photo(message.chat.id, file_info['file_id'], caption=caption, parse_mode=None)
                    elif file_info['type'] == 'document':
                        bot.send_document(message.chat.id, file_info['file_id'], caption=caption, parse_mode=None)
                    elif file_info['type'] == 'audio':
                        bot.send_audio(message.chat.id, file_info['file_id'], caption=caption, parse_mode=None)
                except:
                    pass
            
            time.sleep(0.1)
        
        bot.send_message(message.chat.id, "✅ <b>Barcha fayllar nomlandi!</b>", parse_mode='HTML')
        
        # Ma'lumotlarni tozalash
        user_states[user_id] = None
        if user_id in user_combo_data:
            del user_combo_data[user_id]
    
    else:
        user_states[user_id] = None
        if user_id in user_combo_data:
            del user_combo_data[user_id]
        bot.reply_to(message, "Jarayon to'xtatildi. Yangi buyruq berishingiz mumkin.")


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id, None)
    
    # /textcopy rejimi
    if state == 'textcopy':
        try:
            results = process_textcopy_message(text)
            if results:
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
            else:
                bot.reply_to(message, "❌ Habaringiz xato! Iltimos, quyidagi formatlardan birini ishlating:\n"
                           "• ֎0 - raqam - 1֎\n"
                           "• ֎0 - text - 1֎\n"
                           "• ֎0 - textenter - 1֎")
        except Exception as e:
            bot.reply_to(message, f"❌ Xatolik: {str(e)}")
    
    # /combo rejimi - format kiritish
    elif state == 'combo_format':
        if process_combo_format(text):
            format_type, start_num, pattern_text = get_combo_format_type(text)
            if format_type is None:
                bot.reply_to(
                    message, 
                    "❌ Format xato! Iltimos, ֎1 - raqam֎ yoki ֎1 - text raqam֎ formatidan foydalaning.\n\n"
                    "Masalan:\n"
                    "<b>Video <code>֎1 - raqam֎</code></b> - bilan \n"
                    "<b>Yoki</b>\n"
                    "Video <code>֎1 - text raqam֎</code> - qoshilgan holda habar yuboring",
                    parse_mode='HTML'
                )
                return
            
            user_states[user_id] = 'combo_files'
            user_combo_data[user_id] = {
                'format': text,
                'files': []
            }
            bot.reply_to(
                message, 
                "✅ Habar qabul qilindi!\n\n"
                "📎 Endi video/rasm/fayllarni yuboring.\n"
                "/stop buyrug'i bilan yakunlang."
            )
        else:
            bot.reply_to(
                message, 
                "❌ Format xato! Iltimos, ֎1 - raqam֎ yoki ֎1 - text raqam֎ formatidan foydalaning.\n\n"
                "Masalan:\n"
                "<b>Video <code>֎1 - raqam֎</code></b> - bilan \n"
                "<b>Yoki</b>\n"
                "Video <code>֎1 - text raqam֎</code> - qoshilgan holda habar yuboring",
                parse_mode='HTML'
            )
    
    elif state == 'combo_files':
        bot.reply_to(message, "📎 Iltimos, video/rasm/fayl yuboring yoki /stop buyrug'i bilan yakunlang.")
    else:
        bot.reply_to(message, "To'xtang, avval /textcopy yoki /combo buyrug'ini yuboring.")


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
        
        if file_info:
            user_combo_data[user_id]['files'].append(file_info)
            files_count = len(user_combo_data[user_id]['files'])
            
            bot.reply_to(
                message, 
                f"✅ Fayl qabul qilindi! (Jami: {files_count} ta)\n"
                "/stop buyrug'i bilan yakunlang."
            )
    
    elif state == 'combo_format':
        bot.reply_to(message, "❌ Avval Habaringizni kiriting!")
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
