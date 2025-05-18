from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message

from data.keyboards import buy_sub_keyboard, generate_sub_keyboard
from settings import payment_photo, sub_description_photo
from utils.subscription import check_is_subscribed

sub_management_router = Router()

@sub_management_router.message(Command("subscribe"))
async def handle_sub_command(message: Message, bot: Bot):
    if await check_is_subscribed(message.from_user.id):
        await message.answer("Меню управления подпиской (ещё не готово)")
    else:
        await message.answer_photo(photo=sub_description_photo,
                                   reply_markup=generate_sub_keyboard(mode_type=None, mode_id=None).as_markup())

@sub_management_router.callback_query(F.data.startswith("sub_management"), any_state)
async def sub_management(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await handle_sub_command(call.message, bot)
