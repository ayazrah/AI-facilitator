import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# Таймаут в минутах — если никто не пишет, бот даёт промежуточный анализ
# 0 = таймаут отключён
TIMEOUT_MINUTES = int(os.getenv("TIMEOUT_MINUTES", "30"))

# База данных
DB_PATH = os.getenv("DB_PATH", "bot.db")
