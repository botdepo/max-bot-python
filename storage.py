"""Хранилище заметок в SQLite.

На botdepo писать на диск можно только в /data — эта папка переживает
перезапуски и передеплои. Остальная файловая система только для чтения.
Локально (где /data нет) база ляжет в ./data рядом с кодом.
"""
import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR") or ("/data" if Path("/data").is_dir() else "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

_db = sqlite3.connect(DATA_DIR / "notes.db")
_db.execute(
    """CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )"""
)
_db.commit()


def add_note(user_id: int, text: str) -> int:
    """Сохраняет заметку и возвращает, сколько их теперь у пользователя."""
    _db.execute("INSERT INTO notes (user_id, text) VALUES (?, ?)", (user_id, text))
    _db.commit()
    return _db.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,)).fetchone()[0]


def list_notes(user_id: int, limit: int = 10) -> list[tuple[int, str]]:
    """Последние заметки пользователя: список пар (id, текст)."""
    return _db.execute(
        "SELECT id, text FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()


def delete_note(user_id: int, note_id: int) -> None:
    # user_id в условии — чтобы нельзя было удалить чужую заметку, подставив id
    _db.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    _db.commit()
