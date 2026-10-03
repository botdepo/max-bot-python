"""Стартовый MAX-бот для botdepo: заметки.

Что показывает:
- команды (/start, /list) и обычные текстовые сообщения;
- инлайн-кнопки и обработку нажатий;
- хранение данных в /data (см. storage.py).

Токен бот получает из переменной окружения BOT_TOKEN — на botdepo её
подставляет панель, локально задайте сами (см. README). Библиотека maxapi
сама ищет MAX_BOT_TOKEN, поэтому токен передаём явно.
"""
import asyncio
import logging
import os

from maxapi import Bot, Dispatcher, F
from maxapi.filters.command import Command, CommandStart
from maxapi.types import BotStarted, CallbackButton, MessageCallback, MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

bot = Bot(token=os.environ["BOT_TOKEN"])
dp = Dispatcher()

HELLO = (
    "Привет! Я бот-заметки.\n\n"
    "Пришлите любой текст — сохраню его.\n"
    "/list — показать заметки и удалить ненужные."
)


def notes_view(user_id: int) -> tuple[str, list]:
    """Текст со списком заметок и клавиатура «удалить» (пустой список — без кнопок)."""
    notes = storage.list_notes(user_id)
    if not notes:
        return "Заметок пока нет. Просто пришлите мне текст.", []
    lines = [f"{i}. {text}" for i, (_, text) in enumerate(notes, start=1)]
    kb = InlineKeyboardBuilder()
    for i, (note_id, _) in enumerate(notes, start=1):
        kb.add(CallbackButton(text=f"🗑 {i}", payload=f"del:{note_id}"))
    kb.adjust(5)
    return "Ваши заметки:\n\n" + "\n".join(lines), [kb.as_markup()]


# Пользователь нажал «Начать» в новом чате с ботом
@dp.bot_started()
async def started(event: BotStarted) -> None:
    await bot.send_message(chat_id=event.chat_id, text=HELLO)


@dp.message_created(CommandStart())
async def start(event: MessageCreated) -> None:
    await event.message.answer(HELLO)


@dp.message_created(Command("list"))
async def show_list(event: MessageCreated) -> None:
    text, keyboard = notes_view(event.message.sender.user_id)
    await event.message.answer(text, attachments=keyboard)


@dp.message_created(F.message.body.text)
async def save(event: MessageCreated) -> None:
    text = event.message.body.text
    if text.startswith("/"):
        await event.message.answer("Не знаю такую команду. Есть /start и /list.")
        return
    count = storage.add_note(event.message.sender.user_id, text)
    await event.message.answer(f"Сохранил. Всего заметок: {count}. /list — посмотреть.")


@dp.message_callback()
async def on_button(event: MessageCallback) -> None:
    payload = event.callback.payload or ""
    if payload.startswith("del:"):
        user_id = event.callback.user.user_id
        storage.delete_note(user_id, int(payload.split(":", 1)[1]))
        text, keyboard = notes_view(user_id)
        await event.answer(notification="Удалено", new_text=text, attachments=keyboard)


async def main() -> None:
    me = await bot.get_me()
    logging.info("бот запущен: %s", me.username or me.first_name)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
