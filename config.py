# config.py - Все настройки бота (без токенов, для GitHub)

import os

# ===== ТОКЕНЫ БОТОВ (берутся из переменных окружения) =====
MAIN_BOT_TOKEN = os.environ.get("MAIN_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN")

# ===== GROQ API =====
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ===== ТВОЙ TELEGRAM ID =====
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 0))

# ===== НАСТРОЙКИ БОТА =====
GROQ_MODEL = "llama-3.1-8b-instant"
QUESTIONS_FILE = "questionnaires.json"
