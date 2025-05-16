from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state


sub_management_router = Router()

@sub_management_router.message(Command("subscribe"))
async def handle_sub_command(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await sub_management(call, state, bot)

@sub_management_router.callback_query(F.data.startswith("sub_management"), any_state)
async def sub_management(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.message.answer("Меню управления подпиской (ещё не готово)")
