from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from data.keyboards import referral_keyboard, menu_keyboard
# from data.keyboards import choice_keyboard
# from data.messages import start_message, wait_manager, update_language
from db.repository import referral_system_repository
from settings import InputMessage, start_referral_text
from utils.generate_promo import generate_single_promo_code

referral_router = Router()


@referral_router.callback_query(F.data == "referral_system")
async def referral_system_message(call: CallbackQuery):
    await call.message.answer(text=start_referral_text, reply_markup=referral_keyboard.as_markup())
    await call.message.delete()


@referral_router.callback_query(F.data == "create_promo_code")
async def create_system_message(call: CallbackQuery):
    user_id = call.from_user.id
    promo = await referral_system_repository.get_promo_by_bring_user_id(bring_user_id=user_id)
    if promo is not None:
        await call.message.answer(f"🥜Ты уже <b>выпускал промокод</b>. По одному промокоду может прийти любое количество друзей!\n\n"
                                  f"Твой промокод: <code>{promo.promo_code}</code>",
                                  reply_markup=menu_keyboard.as_markup())
        await call.message.delete()
        return
    promo_code = await generate_single_promo_code()
    await referral_system_repository.add_promo(bring_user_id=user_id, promo_code=promo_code)
    await call.message.answer(f"Отлично, ты выпустил новый промокод: <code>{promo_code}</code>. Твоим друзьям достаточно"
                              f" ввести этот промокод, чтобы и ты, и они получили свои бонусы)",
                              reply_markup=menu_keyboard.as_markup())
    await call.message.delete()


@referral_router.callback_query(F.data == "enter_promo_code")
async def enter_promo_code_message(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    delete_message = await call.message.answer("🥜Отлично — введи <b>промокод</b>, который тебе передал твой друг!",
                              reply_markup=menu_keyboard.as_markup())
    await state.set_state(InputMessage.enter_promo)
    await state.update_data(message_delete_id = delete_message.message_id, from_referral=True)