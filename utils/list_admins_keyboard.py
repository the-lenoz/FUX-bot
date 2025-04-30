from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.repository import admin_repository


class Admins_kb:
    async def generate_list(self):
        admins = await admin_repository.select_all_admins()
        keyboard = InlineKeyboardBuilder()
        for admin in admins:
            keyboard.row(InlineKeyboardButton(text=f"{admin.username}", callback_data=f"admin|{admin.admin_id}"))
        keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        return keyboard