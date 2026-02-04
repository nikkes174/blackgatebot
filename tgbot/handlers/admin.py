import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tgbot.keyboards.inline import admin_panel

admin_router = Router()

ADMINS = [
    int(x) for x in os.getenv("ADMINS", "").split(",") if x
]


@admin_router.message(Command("admin_panel"))
async def open_admin_panel(message: Message):
    user_id = message.from_user.id

    if user_id not in ADMINS:
        await message.answer("⛔️ Нет доступа")
        return

    await message.answer(
        "🛠 Панель администратора",
        reply_markup=admin_panel()
    )


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS
