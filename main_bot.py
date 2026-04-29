# main_bot.py - Полностью рабочий код с Groq

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import json
import os
import time
from datetime import datetime
from groq import Groq  # 👈 НОВАЯ БИБЛИОТЕКА
from config import *

# ===== НАСТРОЙКА GROQ =====
client = Groq(api_key=GROQ_API_KEY)

main_bot = telebot.TeleBot(MAIN_BOT_TOKEN)
admin_bot = telebot.TeleBot(ADMIN_BOT_TOKEN)

# Хранилище данных
user_data = {}
chat_histories = {}
completed_users = set()

# ==================== КЛАВИАТУРЫ ====================

def get_gender_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Мужской"),
        KeyboardButton("Женский"),
        KeyboardButton("Другой"),
        KeyboardButton("Не хочу указывать")
    )
    return keyboard

def get_relationship_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Да, в отношениях"),
        KeyboardButton("Нет, свободен(а)"),
        KeyboardButton("В активном поиске")
    )
    return keyboard

def get_continue_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("✅ Заполнить анкету"),
        KeyboardButton("❌ Отказаться")
    )
    return keyboard

# ==================== ЗАГРУЗКА ====================

def load_completed_users():
    global completed_users
    if os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                questionnaires = json.load(f)
                for q in questionnaires:
                    completed_users.add(q['user_id'])
            print(f"📊 Загружено {len(completed_users)} пользователей из JSON")
        except Exception as e:
            print(f"Ошибка загрузки JSON: {e}")

def is_questionnaire_completed(user_id):
    return user_id in completed_users

def mark_questionnaire_completed(user_id):
    completed_users.add(user_id)
    print(f"✅ Пользователь {user_id} отмечен как заполнивший анкету")

def calculate_age(birth_date_str):
    """Вычисляет возраст по дате рождения в формате ДД.ММ.ГГГГ"""
    try:
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y")
        today = datetime.now()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except:
        return None

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@main_bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    print(f"📱 /start от пользователя {user_id} ({user_name})")
    
    if is_questionnaire_completed(user_id):
        if user_id not in chat_histories:
            chat_histories[user_id] = []
            load_user_data_from_json(user_id)
        
        main_bot.send_message(
            user_id,
            f"✨ С возвращением, {user_name}! ✨\n\n"
            "Твоя анкета уже есть в базе ✅\n"
            "Теперь ты можешь общаться со мной!\n\n"
            "Просто напиши любой вопрос 🤖💬"
        )
        return
    
    user_data[user_id] = {'step': 'start'}
    
    welcome_text = f"""✨ Привет, {user_name}! ✨

Я бот на базе Groq с нейросетью Llama! 🦙

Пожалуйста, заполни небольшую анкету.

Нажми на кнопку ниже, чтобы начать:"""
    
    main_bot.send_message(
        user_id,
        welcome_text,
        reply_markup=get_continue_keyboard()
    )

@main_bot.message_handler(func=lambda message: message.text == "✅ Заполнить анкету")
def start_questionnaire(message):
    user_id = message.from_user.id
    print(f"📝 Начало анкеты для {user_id}")
    user_data[user_id] = {'step': 'name'}
    main_bot.send_message(
        user_id,
        "📝 Как тебя зовут?",
        reply_markup=ReplyKeyboardRemove()
    )

@main_bot.message_handler(func=lambda message: message.text == "❌ Отказаться")
def decline_questionnaire(message):
    user_id = message.from_user.id
    main_bot.send_message(
        user_id, 
        "❌ Жаль! Напиши /start, если передумаешь",
        reply_markup=ReplyKeyboardRemove()
    )
    if user_id in user_data:
        del user_data[user_id]

# ==================== АНКЕТА ====================

@main_bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id].get('step') not in ['completed', 'chat'])
def handle_questionnaire(message):
    user_id = message.from_user.id
    text = message.text.strip()
    step = user_data[user_id].get('step', 'name')
    
    print(f"📝 Анкета шаг {step}: {text[:50]}")
    
    if step == 'name':
        if text:
            user_data[user_id]['name'] = text
            user_data[user_id]['step'] = 'birth_date'
            main_bot.send_message(
                user_id,
                "🎂 Введи свою дату рождения в формате **ДД.ММ.ГГГГ**\n\n"
                "Например: `15.08.2005`",
                parse_mode="Markdown"
            )
    
    elif step == 'birth_date':
        age = calculate_age(text)
        
        if age is not None:
            user_data[user_id]['birth_date'] = text
            user_data[user_id]['age'] = age
            
            if age < 18:
                main_bot.send_message(
                    user_id,
                    "🚫 **ДОСТУП ЗАПРЕЩЁН!** 🚫\n\n"
                    "❌ Вам нет 18 лет!\n"
                    "Идите лучше уроки учите! 📚",
                    parse_mode="Markdown"
                )
                time.sleep(1.5)
                main_bot.send_message(
                    user_id,
                    "😜 **Ладно, это была шутка!**\n\n"
                    "На самом деле мы всем рады! 🎒",
                    parse_mode="Markdown"
                )
                time.sleep(1)
                main_bot.send_message(
                    user_id,
                    f"🎉 Тебе всего {age} лет! Целая жизнь впереди!\n"
                    "Продолжаем анкету...",
                    parse_mode="Markdown"
                )
                time.sleep(1)
            else:
                main_bot.send_message(
                    user_id,
                    f"🍷 **Ого! {age} лет!** 🍷\n\n"
                    "Взрослый человек, солидный возраст!\n"
                    "Шучу, конечно! Рад видеть! 🎩",
                    parse_mode="Markdown"
                )
                time.sleep(1.5)
                main_bot.send_message(
                    user_id,
                    f"🔥 Ты в самом расцвете сил! 💪\n\nПродолжаем анкету...",
                    parse_mode="Markdown"
                )
                time.sleep(1)
            
            user_data[user_id]['step'] = 'gender'
            main_bot.send_message(user_id, "👤 Твой пол:", reply_markup=get_gender_keyboard())
        else:
            main_bot.send_message(
                user_id,
                "❌ Неправильный формат даты!\n"
                "Введи дату в формате **ДД.ММ.ГГГГ**\n\n"
                "Пример: `15.08.2005`",
                parse_mode="Markdown"
            )
    
    elif step == 'gender':
        if text in ["Мужской", "Женский", "Другой", "Не хочу указывать"]:
            user_data[user_id]['gender'] = text
            user_data[user_id]['step'] = 'relationship'
            main_bot.send_message(
                user_id,
                "💑 Ты сейчас в отношениях?",
                reply_markup=get_relationship_keyboard()
            )
        else:
            main_bot.send_message(user_id, "❌ Выбери из кнопок")
    
    elif step == 'relationship':
        valid_options = ["Да, в отношениях", "Нет, свободен(а)", "В активном поиске"]
        if text in valid_options:
            user_data[user_id]['relationship'] = text
            
            if text == "Да, в отношениях":
                main_bot.send_message(
                    user_id,
                    "🤨 **ПОДОЗРИТЕЛЬНО...**\n\n"
                    "Тут вообще-то клуб свободных сигм 🦅\n"
                    "Но ладно, сделаем исключение! 😏",
                    parse_mode="Markdown"
                )
                time.sleep(1.5)
                main_bot.send_message(
                    user_id,
                    "😜 Шучу! Любовь — это круто 💕",
                    parse_mode="Markdown"
                )
                time.sleep(1)
            elif text == "Нет, свободен(а)":
                main_bot.send_message(
                    user_id,
                    "🦅 **О, ДА! НАСТОЯЩИЙ СИГМА!** 🦅\n\n"
                    "✅ Анкета принята! Респект за честность! 🔥",
                    parse_mode="Markdown"
                )
                time.sleep(1.5)
                main_bot.send_message(
                    user_id,
                    "😎 Свобода — это круто! Продолжаем...",
                    parse_mode="Markdown"
                )
                time.sleep(1)
            else:
                main_bot.send_message(
                    user_id,
                    "🔍 **ОХОТНИК ЗА ЛЮБОВЬЮ!** 🔍\n\n"
                    "Ты как детектив, ищешь свою половинку 🕵️\n"
                    "Лови удачу! 🍀",
                    parse_mode="Markdown"
                )
                time.sleep(1.5)
                main_bot.send_message(
                    user_id,
                    "😄 Продолжаем анкету!",
                    parse_mode="Markdown"
                )
                time.sleep(1)
            
            user_data[user_id]['step'] = 'completed'
            save_and_send_to_admin(user_id)
            start_groq_chat(user_id)
        else:
            main_bot.send_message(user_id, "❌ Выбери из кнопок")

# ==================== ЗАПУСК GROQ ====================

def start_groq_chat(user_id):
    data = user_data.get(user_id, {})
    name = data.get('name', 'Пользователь')
    age = data.get('age', 'неизвестно')
    
    print(f"🤖 Запуск Groq для {user_id} (имя: {name}, возраст: {age})")
    
    mark_questionnaire_completed(user_id)
    
    main_bot.send_message(
        user_id,
        f"🤖 **Отлично, {name}! Анкета заполнена!** 🤖\n\n"
        f"📊 Твой возраст: {age} лет\n"
        "Теперь я отвечаю на любые вопросы через нейросеть Llama!\n\n"
        "Просто напиши что-нибудь. Например:\n"
        "• Сколько людей на Земле?\n"
        "• Расскажи шутку\n"
        "• Что такое любовь?\n\n"
        "Погнали! 🚀",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    gender = data.get('gender', 'не указан')
    relationship = data.get('relationship', 'не указан')
    
    chat_histories[user_id].append({
        "role": "system",
        "content": f"Пользователя зовут {name}, ему {age} лет, пол: {gender}, статус отношений: {relationship}. Отвечай дружелюбно и полезно."
    })
    
    if user_id in user_data:
        del user_data[user_id]

# ==================== ОБЩЕНИЕ С GROQ ====================

@main_bot.message_handler(func=lambda message: True)
def chat_with_groq(message):
    user_id = message.from_user.id
    user_text = message.text
    
    print(f"💬 Получено сообщение от {user_id}: {user_text[:50]}")
    
    if user_text.startswith('/'):
        return
    
    if is_questionnaire_completed(user_id):
        main_bot.send_chat_action(user_id, 'typing')
        
        try:
            # 👇 ЗАПРОС К GROQ
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            answer = response.choices[0].message.content
            
            if not answer or len(answer.strip()) == 0:
                answer = "Извини, не могу ответить на этот вопрос. Попробуй спросить что-то другое!"
            
            if user_id not in chat_histories:
                chat_histories[user_id] = []
            
            chat_histories[user_id].append({"role": "user", "content": user_text})
            chat_histories[user_id].append({"role": "assistant", "content": answer})
            
            if len(chat_histories[user_id]) > 30:
                chat_histories[user_id] = chat_histories[user_id][-30:]
            
            main_bot.send_message(user_id, answer)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Groq ошибка: {error_msg}")
            
            if "429" in error_msg:
                main_bot.send_message(user_id, "📊 Слишком много запросов. Подожди немного.")
            else:
                main_bot.send_message(user_id, f"❌ Ошибка: {error_msg[:100]}")
    
    else:
        main_bot.send_message(
            user_id,
            "📋 Пожалуйста, сначала заполни анкету!\nНапиши /start, чтобы начать."
        )

# ==================== ЗАГРУЗКА ДАННЫХ ====================

def load_user_data_from_json(user_id):
    if not os.path.exists(QUESTIONS_FILE):
        return
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            questionnaires = json.load(f)
            for q in questionnaires:
                if q['user_id'] == user_id:
                    answers = q.get('answers', {})
                    chat_histories[user_id] = [{
                        "role": "system",
                        "content": f"Пользователь: {answers.get('name', 'Пользователь')}, {answers.get('age', '?')} лет"
                    }]
                    break
    except Exception as e:
        print(f"Ошибка загрузки: {e}")

def save_and_send_to_admin(user_id):
    data = user_data.get(user_id, {})
    if not data:
        return
    
    try:
        chat = main_bot.get_chat(user_id)
        username = f"@{chat.username}" if chat.username else "Не указан"
        full_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip()
    except:
        username = "Неизвестно"
        full_name = "Не удалось получить"
    
    age = data.get('age', 0)
    age_category = "👶 Несовершеннолетний" if age < 18 else "👨 Взрослый"
    
    questionnaire_text = f"""
📋 **НОВАЯ АНКЕТА** 📋

👤 {full_name} ({username})
🆔 ID: `{user_id}`

📝 **Ответы:**
• Имя: **{data.get('name', '?')}**
• Дата рождения: **{data.get('birth_date', '?')}**
• Возраст: **{age}** лет ({age_category})
• Пол: **{data.get('gender', '?')}**
• Отношения: **{data.get('relationship', '?')}**

⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
    """
    
    questionnaires = []
    if os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                questionnaires = json.load(f)
        except:
            pass
    
    for q in questionnaires:
        if q['user_id'] == user_id:
            return
    
    new_entry = {
        'user_id': user_id,
        'username': username,
        'full_name': full_name,
        'timestamp': datetime.now().isoformat(),
        'answers': {
            'name': data.get('name'),
            'birth_date': data.get('birth_date'),
            'age': data.get('age'),
            'gender': data.get('gender'),
            'relationship': data.get('relationship')
        }
    }
    questionnaires.append(new_entry)
    
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(questionnaires, f, ensure_ascii=False, indent=2)
    
    try:
        admin_bot.send_message(ADMIN_CHAT_ID, questionnaire_text, parse_mode='Markdown')
        print(f"✅ Анкета {user_id} отправлена админу")
    except Exception as e:
        print(f"❌ Ошибка отправки админу: {e}")

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    load_completed_users()
    
    print("=" * 50)
    print("🚀 СИГМА-БОТ ЗАПУЩЕН!")
    print("=" * 50)
    print(f"📱 Основной бот активен")
    print(f"🤖 Модель: {GROQ_MODEL}")
    print(f"👑 Админ ID: {ADMIN_CHAT_ID}")
    print(f"📊 Пользователей в базе: {len(completed_users)}")
    print("=" * 50)
    print("🎯 Используется Groq API!")
    print("   ✅ Лимит: 30 запросов/минуту, 14400 запросов/день")
    print("=" * 50)
    
    try:
        main_bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
