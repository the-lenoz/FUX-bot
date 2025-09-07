from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.deep_linking import create_start_link

from data.keyboards import referral_keyboard, menu_keyboard, generate_gift_keyboard
from db.repository import referral_system_repository
from data.message_templates import messages_dict
from utils.generate_promo import generate_single_promo_code
from utils.state_models import InputMessage

referral_router = Router()


@referral_router.callback_query(F.data == "referral_system")
async def referral_system_message(call: CallbackQuery):
    await call.message.answer(text=messages_dict["start_referral_text"], reply_markup=referral_keyboard.as_markup())
    await call.message.delete()


@referral_router.message(Command("referral"))
async def referral_command_handler(message: Message, bot: Bot):
    await message.answer(text=messages_dict["start_referral_text"], reply_markup=referral_keyboard.as_markup())


@referral_router.callback_query(F.data == "create_promo_code")
async def create_system_message(call: CallbackQuery):
    user_id = call.from_user.id
    promo = await referral_system_repository.get_promo_by_bring_user_id(bring_user_id=user_id)
    if promo is not None:
        referral_link = await create_start_link(call.bot, promo.promo_code)
        await call.message.answer(f"🥜Ты уже <b>выпускал промокод</b>. По одному промокоду может прийти любое количество друзей!\n\n"
                                  f"Твой промокод: <code>{promo.promo_code}</code>\n"
                                  f"Твоя реферальная ссылка: {referral_link}",

                                  reply_markup=menu_keyboard.as_markup())
    else:
        promo_code = await generate_single_promo_code()
        await referral_system_repository.add_promo(bring_user_id=user_id, promo_code=promo_code)
        referral_link = await create_start_link(call.bot, promo_code)
        await call.message.answer(f"Отлично, ты выпустил новый промокод: <code>{promo_code}</code>. Твоим друзьям достаточно"
                                  f" ввести этот промокод либо нажать на реферальную ссылку: {referral_link}, чтобы и ты, и они получили свои бонусы)",
                                  reply_markup=menu_keyboard.as_markup())
    await call.message.delete()


@referral_router.callback_query(F.data == "enter_promo_code")
async def enter_promo_code_message(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    delete_message = await call.message.answer("🥜Отлично — введи <b>промокод</b>, который тебе передал твой друг!",
                              reply_markup=menu_keyboard.as_markup())
    await state.set_state(InputMessage.enter_promo)
    await state.update_data(message_delete_id = delete_message.message_id, from_referral=True)

@referral_router.callback_query(F.data == "buy_gift")
async def enter_promo_code_message(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        text="Выбери, что подаришь другу!",
        reply_markup=(await generate_gift_keyboard(call.from_user.id)).as_markup()
    )
    await call.message.delete()

