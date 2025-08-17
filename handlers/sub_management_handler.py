from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.messages_provider import send_subscription_management_menu

sub_management_router = Router()

@sub_management_router.message(Command("subscribe"))
async def handle_sub_command(message: Message, bot: Bot):
    await send_subscription_management_menu(message.from_user.id)

@sub_management_router.callback_query(F.data.startswith("subscribe"), any_state)
@sub_management_router.callback_query(F.data.startswith("sub_management"), any_state)
async def sub_management(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.message.delete()
    await send_subscription_management_menu(call.from_user.id)


@sub_management_router.callback_query(F.data.startswith("cancel_subscription"), any_state)
async def sub_management(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    confirm = int(call.data.split("|")[-1])
    if confirm == 2:
        pass
    elif confirm == 1:
        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.row(
            InlineKeyboardButton(text="Да", callback_data="cancel_subscription|2")
        )
        keyboard_builder.row(
            InlineKeyboardButton(text="нет", callback_data="sub_management")
        )
        await call.message.answer(
            "Ты ",
            reply_markup=keyboard_builder.as_markup()
        )
    else:
        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.row(
            InlineKeyboardButton(text="Да", callback_data="cancel_subscription|1")
        )
        keyboard_builder.row(
            InlineKeyboardButton(text="нет", callback_data="sub_management")
        )
        await send_subscription_management_menu(call.from_user.id)
    await call.message.delete()
