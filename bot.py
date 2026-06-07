import os
import re
import time
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_states = {}
user_combo_data = {}


def process_textcopy_message(text):
    results = []
    
    raqam_pattern = r'(\d+)\s*-\s*raqam\s*-\s*(\d+)'
    text_pattern = r'(\d+)\s*-\s*text\s*-\s*(\d+)'
    textenter_pattern = r'(\d+)\s*-\s*textenter\s*-\s*(\d+)'
    
    for match in re.finditer(raqam_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        for i in range(start, start + count):
            msg = template.format(i)
            results.append(("individual", msg, 'HTML'))
    
    for match in re.finditer(text_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        parts = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", ", ".join(parts), 'HTML'))
    
    for match in re.finditer(textenter_pattern, text):
        start = int(match.group(1))
        count = int(match.group(2))
        template = text.replace(match.group(0), '{}').strip()
        lines = [template.format(i) for i in range(start, start + count)]
        results.append(("combined", "\n".join(lines), 'HTML'))
    
    return results


def process_combo_format(text):
    raqam_pattern = r'(\d+)\s*-\s*raqam'
    text_raqam_pattern = r'(\d+)\s*-\s*text\s*raqam'
    
    has_raqam = bool(re.search(raqam_pattern, text))
    has_text_raqam = bool(re.search(text_raqam_pattern, text))
    
    return has_raqam or has_text_raqam


def get_combo_format_type(text):
    raqam_pattern = r'(\d+)\s*-\s*raqam'
    text_raqam_pattern = r'(\d+)\s*-\s*text\s*raqam'
    
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
📝 <b>TextCopy - Matn nusxalash</b>

<b>Formatlar:</b>
1️⃣ <code>0 - raqam - 5</code> - Alohida xabarlar
2️⃣ <code>0 - text - 5</code> - Bitta xabarda yonma-yon
3️⃣ <code>0 - textenter - 5</code> - Yangi qatordan

<b>Misol:</b>
<code>Anime nomi 1 - raqam - 3-qism</code>

✍️ <b>Endi matn yuboring!</b>
"""
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(commands=['combo'])
def cmd_combo(message):
    user_id = message.from_user.id
    user_states[user_id] = 'combo_format'
    
    help_text = """
📁 <b>Combo - Fayllarni nomlash</b>

<b>Formatlar:</b>
1️⃣ <code>1 - raqam</code> - Raqam bilan
2️⃣ <code>1 - text raqam</code> - Matn va raqam bilan

<b>Misol:</b>
<code>Video 1 - raqam</code>

✍️ <b>Endi formatni yuboring!</b>
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
        
        bot.reply_to(message, f"✅ <b>{len(files)} ta fayl qabul qilindi. Nomlash boshlandi...</b>", parse_mode='HTML')
        
        for idx, file_info in enumerate(files):
            number = start_num + idx
            caption = format_text.replace(pattern_text, str(number))
            
            parse = 'HTML' if format_type == 'raqam' else None
            
            try:
                if file_info['type'] == 'video':
                    bot.send_video(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
                elif file_info['type'] == 'photo':
                    bot.send_photo(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
                elif file_info['type'] == 'document':
                    bot.send_document(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
                elif file_info['type'] == 'audio':
                    bot.send_audio(message.chat.id, file_info['file_id'], caption=caption, parse_mode=parse)
            except:
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
        
        user_states[user_id] = None
        if user_id in user_combo_data:
            del user_combo_data[user_id]
    else:
        user_states[user_id] = None
        if user_id in user_combo_data:
            del user_combo_data[user_id]
        bot.reply_to(message, "✅ Jarayon to'xtatildi.")


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id, None)
    
    if state == 'textcopy':
        if '- raqam -' in text or '- text -' in text or '- textenter -' in text:
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
                    bot.reply_to(message, "❌ Format xato! Misol: <code>Anime 1 - raqam - 3-qism</code>", parse_mode='HTML')
            except Exception as e:
                bot.reply_to(message, f"❌ Xatolik: {str(e)}")
        else:
            bot.reply_to(message, "❌ Format topilmadi! Misol: <code>test 0 - raqam - 3</code>", parse_mode='HTML')
    
    elif state == 'combo_format':
        if process_combo_format(text):
            user_states[user_id] = 'combo_files'
            user_combo_data[user_id] = {
                'format': text,
                'files': []
            }
            bot.reply_to(message, "✅ Qabul qilindi!\n\n📎 Endi fayllarni yuboring.\n/stop bilan yakunlang.")
        else:
            bot.reply_to(message, "❌ Format xato! Misol: <code>Video 1 - raqam</code>", parse_mode='HTML')
    
    elif state == 'combo_files':
        bot.reply_to(message, "📎 Fayl yuboring yoki /stop bosing.")
    else:
        bot.reply_to(message, "Avval /textcopy yoki /combo buyrug'ini yuboring.")


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
            count = len(user_combo_data[user_id]['files'])
            bot.reply_to(message, f"✅ Qabul qilindi! (Jami: {count} ta)\n/stop bilan yakunlang.")
    elif state == 'combo_format':
        bot.reply_to(message, "❌ Avval formatni kiriting!")
    else:
        bot.reply_to(message, "Avval /combo buyrug'ini yuboring.")


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 403


@app.route('/')
def index():
    return "Bot is running 24/7!"


if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    
    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if render_url:
        webhook_url = f"{render_url}/webhook"
        bot.set_webhook(url=webhook_url)
        print(f"Webhook: {webhook_url}")
    
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
