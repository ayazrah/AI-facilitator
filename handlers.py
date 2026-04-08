import os
import tempfile
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    create_session, get_session, save_message,
    get_messages, reset_session
)
from ai import analyze, client
import scheduler as sched

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
    sched.notified.discard(msg.chat.id)

    await msg.answer(
        f"{PRIVACY_NOTICE}"
        f"📌 *Вопрос для обсуждения:*\n_{question}_\n\n"
        "Участники — пишите ваши мысли прямо в чат.\n"
        "Текст и голосовые — всё принимается.\n"
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

    # Закрываем сессию — таймаут больше не сработает
    await reset_session(msg.chat.id)
    sched.notified.discard(msg.chat.id)


@router.message(Command("reset"))
async def cmd_reset(msg: Message):
    await reset_session(msg.chat.id)
    sched.notified.discard(msg.chat.id)
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


@router.message(F.voice)
async def collect_voice(msg: Message):
    session = await get_session(msg.chat.id)
    if not session:
        return

    await msg.reply("🎤 Транскрибирую...")

    # Скачиваем голосовое во временный файл
    file = await msg.bot.get_file(msg.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await msg.bot.download_file(file.file_path, tmp.name)
        tmp_path = tmp.name

    try:
        # Транскрибируем через Whisper
        with open(tmp_path, "rb") as audio:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        text = transcript.text.strip()

        if not text:
            await msg.reply("Не удалось распознать голосовое сообщение.")
            return

        # Сохраняем как обычное текстовое сообщение
        username = msg.from_user.username or msg.from_user.full_name
        await save_message(msg.chat.id, username, text)

        # Показываем транскрипцию в чате
        await msg.reply(
            f"🎤 *{username}:*\n_{text}_",
            parse_mode="Markdown"
        )

    except Exception as e:
        await msg.reply(f"Ошибка транскрибации: {e}")
    finally:
        os.unlink(tmp_path)


@router.message(F.text & ~F.text.startswith("/"))
async def collect_message(msg: Message):
    session = await get_session(msg.chat.id)
    if not session:
        return

    username = msg.from_user.username or msg.from_user.full_name
    await save_message(msg.chat.id, username, msg.text)
