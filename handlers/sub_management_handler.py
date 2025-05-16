from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message

sub_management_router = Router()

@sub_management_router.message(Command("subscribe"))
async def handle_sub_command(message: Message, bot: Bot):
    await message.answer("Меню управления подпиской (ещё не готово)")

@sub_management_router.callback_query(F.data.startswith("sub_management"), any_state)
async def sub_management(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await handle_sub_command(call.message, bot)
