# SystemBot — AI-фасилитатор групповых обсуждений

Telegram-бот который собирает мнения участников и анализирует их
через системное мышление (по Донелле Медоуз).

## Быстрый старт

### 1. Клонируй и установи зависимости

```bash
git clone <repo>
cd systembot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настрой переменные окружения

```bash
cp .env.example .env
# Открой .env и вставь свои токены
```

**BOT_TOKEN** — получи у [@BotFather](https://t.me/BotFather):
- Напиши `/newbot`
- Придумай имя и username
- Скопируй токен

**OPENAI_API_KEY** — получи на [platform.openai.com](https://platform.openai.com/api-keys)

### 3. Запусти

```bash
python bot.py
```

## Команды бота

| Команда | Что делает |
|---|---|
| `/start Ваш вопрос` | Начинает обсуждение, задаёт вопрос |
| `/preview` | Промежуточный анализ (обсуждение продолжается) |
| `/conclude` | Финальный анализ и закрытие |
| `/reset` | Очистить историю, начать заново |
| `/status` | Текущий вопрос и число сообщений |

## Настройки (файл .env)

- `TIMEOUT_MINUTES` — через сколько минут тишины бот даст промежуточный анализ (0 = отключить)

## Деплой на Railway

1. Залей код на GitHub
2. Зайди на [railway.app](https://railway.app) и подключи репозиторий
3. В настройках добавь переменные из `.env`
4. Railway сам запустит бота

## Деплой на Oracle Cloud (бесплатно навсегда)

1. Зарегистрируйся на [cloud.oracle.com](https://cloud.oracle.com)
2. Создай VM: Always Free, Ubuntu 22.04, ARM
3. Подключись по SSH, установи Python 3.11+
4. Скопируй файлы, настрой `.env`
5. Запусти через `screen` или `systemd`
