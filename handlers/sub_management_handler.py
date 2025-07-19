from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message

from bots import main_bot
from data.keyboards import generate_sub_keyboard
from settings import sub_description_photo
from utils.subscription import check_is_subscribed

sub_management_router = Router()

@sub_management_router.message(Command("subscribe"))
async def handle_sub_command(message: Message, bot: Bot):
    await subscription_management_menu(message.from_user.id)

@sub_management_router.callback_query(F.data.startswith("sub_management"), any_state)
async def sub_management(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await subscription_management_menu(call.from_user.id)


async def subscription_management_menu(user_id: int):
    if await check_is_subscribed(user_id):
        await main_bot.send_message(user_id, "Вы можете продлить <b>подписку</b>:",
                                    reply_markup=generate_sub_keyboard().as_markup())
    else:
        await main_bot.send_photo(user_id,
                                    photo=sub_description_photo,
                                    reply_markup=generate_sub_keyboard().as_markup())