from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    create_session, get_session, save_message,
    get_messages, reset_session
)
from ai import analyze

router = Router()

PRIVACY_NOTICE = (
    "🔒 *Уведомление о приватности*\n"
    "Сообщения этого обсуждения будут переданы в OpenAI для анализа.\n"
    "Продолжая — участники соглашаются с этим.\n\n"
)


@router.message(Command("start"))
async def cmd_start(msg: Message):
    question = msg.text.removeprefix("/start").strip()

    if not question:
        await msg.answer(
            "👋 Привет! Чтобы начать обсуждение, напиши вопрос после команды:\n\n"
            "/start Стоит ли нам нанять ещё одного разработчика?\n\n"
            "Команды:\n"
            "/preview — промежуточный анализ\n"
            "/conclude — финальный анализ\n"
            "/reset — очистить обсуждение\n"
            "/status — текущий вопрос и число сообщений"
        )
        return

    username = msg.from_user.username or msg.from_user.full_name
    await create_session(msg.chat.id, question, username)

    await msg.answer(
        f"{PRIVACY_NOTICE}"
        f"📌 *Вопрос для обсуждения:*\n_{question}_\n\n"
        "Участники — пишите ваши мысли прямо в чат.\n"
        "Когда закончите — /conclude для финального анализа.",
        parse_mode="Markdown"
    )


@router.message(Command("preview"))
async def cmd_preview(msg: Message):
    session = await get_session(msg.chat.id)
    if not session:
        await msg.answer("Нет активного обсуждения. Начни с /start Твой вопрос")
        return

    messages = await get_messages(msg.chat.id)
    await msg.answer("🔍 Анализирую обсуждение...")

    result = await analyze(session["question"], messages, mode="preview")
    await msg.answer(result, parse_mode="Markdown")


@router.message(Command("conclude"))
async def cmd_conclude(msg: Message):
    session = await get_session(msg.chat.id)
    if not session:
        await msg.answer("Нет активного обсуждения. Начни с /start Твой вопрос")
        return

    messages = await get_messages(msg.chat.id)
    if not messages:
        await msg.answer("Пока никто ничего не написал. Дай участникам время.")
        return

    await msg.answer("🔍 Провожу финальный анализ...")
    result = await analyze(session["question"], messages, mode="conclude")
    await msg.answer(result, parse_mode="Markdown")


@router.message(Command("reset"))
async def cmd_reset(msg: Message):
    await reset_session(msg.chat.id)
    await msg.answer(
        "🗑 Обсуждение очищено. Начни новое с /start Твой вопрос"
    )


@router.message(Command("status"))
async def cmd_status(msg: Message):
    session = await get_session(msg.chat.id)
    if not session:
        await msg.answer("Нет активного обсуждения. Начни с /start Твой вопрос")
        return

    messages = await get_messages(msg.chat.id)
    usernames = list({m["username"] for m in messages})

    await msg.answer(
        f"📌 *Вопрос:* _{session['question']}_\n"
        f"💬 Сообщений: {len(messages)}\n"
        f"👥 Участников: {len(usernames)}\n"
        f"🕐 Начато: {session['started_at'][:16]}",
        parse_mode="Markdown"
    )


@router.message(F.text & ~F.text.startswith("/"))
async def collect_message(msg: Message):
    session = await get_session(msg.chat.id)
    if not session:
        return  # нет активной сессии — игнорируем

    username = msg.from_user.username or msg.from_user.full_name
    await save_message(msg.chat.id, username, msg.text)
