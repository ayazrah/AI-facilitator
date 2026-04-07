import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from config import TIMEOUT_MINUTES
from database import get_stale_sessions, get_messages
from ai import analyze

logger = logging.getLogger(__name__)

# Храним чаты которым уже отправили таймаут-анализ
# чтобы не спамить при каждой проверке
_notified: set[int] = set()


async def check_timeouts(bot: Bot):
    if TIMEOUT_MINUTES == 0:
        return

    stale = await get_stale_sessions(TIMEOUT_MINUTES)
    for session in stale:
        chat_id = session["chat_id"]
        if chat_id in _notified:
            continue

        messages = await get_messages(chat_id)
        if not messages:
            continue

        try:
            result = await analyze(session["question"], messages, mode="timeout")
            await bot.send_message(chat_id, result, parse_mode="Markdown")
            _notified.add(chat_id)
            logger.info(f"Timeout analysis sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send timeout analysis to {chat_id}: {e}")


def start_scheduler(bot: Bot):
    if TIMEOUT_MINUTES == 0:
        logger.info("Timeout scheduler disabled (TIMEOUT_MINUTES=0)")
        return

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_timeouts,
        trigger="interval",
        minutes=5,  # проверяем каждые 5 минут
        args=[bot]
    )
    scheduler.start()
    logger.info(f"Scheduler started, timeout = {TIMEOUT_MINUTES} min")
