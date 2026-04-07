import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id     INTEGER PRIMARY KEY,
                question    TEXT NOT NULL,
                started_by  TEXT NOT NULL,
                started_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_msg_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active      INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id    INTEGER NOT NULL,
                username   TEXT NOT NULL,
                text       TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def create_session(chat_id: int, question: str, started_by: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO sessions (chat_id, question, started_by, active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(chat_id) DO UPDATE SET
                question    = excluded.question,
                started_by  = excluded.started_by,
                started_at  = CURRENT_TIMESTAMP,
                last_msg_at = CURRENT_TIMESTAMP,
                active      = 1
        """, (chat_id, question, started_by))
        await db.commit()


async def get_session(chat_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sessions WHERE chat_id = ? AND active = 1", (chat_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def save_message(chat_id: int, username: str, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, username, text) VALUES (?, ?, ?)",
            (chat_id, username, text)
        )
        await db.execute(
            "UPDATE sessions SET last_msg_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
            (chat_id,)
        )
        await db.commit()


async def get_messages(chat_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT username, text, created_at FROM messages
               WHERE chat_id = ? ORDER BY created_at ASC""",
            (chat_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def reset_session(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE sessions SET active = 0 WHERE chat_id = ?", (chat_id,)
        )
        await db.execute(
            "DELETE FROM messages WHERE chat_id = ?", (chat_id,)
        )
        await db.commit()


async def get_stale_sessions(timeout_minutes: int) -> list[dict]:
    """Возвращает активные сессии где никто не писал дольше timeout_minutes."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM sessions
            WHERE active = 1
              AND (strftime('%s','now') - strftime('%s', last_msg_at)) > ?
        """, (timeout_minutes * 60,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
