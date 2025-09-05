import datetime
from datetime import timezone

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.utils.deep_linking import create_start_link

from data.keyboards import cancel_keyboard, menu_keyboard, keyboard_for_pay
from db.repository import users_repository, subscriptions_repository, operation_repository, payment_methods_repository, \
    referral_system_repository
from settings import you_fooher_photo, sub_description_photo_after
from utils.callbacks import subscribed_callback
from utils.generate_promo import generate_single_promo_code
from utils.messages_provider import send_invoice, send_subscription_management_menu, send_prolong_subscription_message
from utils.payment_for_services import check_payment, get_payment_method_id
from utils.price_provider import get_price_for_user
from utils.state_models import InputMessage
from utils.validators import is_valid_email

payment_router = Router()


@payment_router.callback_query(F.data.startswith("choice_sub"), any_state)
async def get_choice_of_sub(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    call_data = call.data.split("|")
    days, mode_type = call_data[1], call_data[2]
    user = await users_repository.get_user_by_user_id(call.from_user.id)
    amount = await get_price_for_user(user_id=user.user_id, plan=int(days))
    if user.email is None:
        await state.set_state(InputMessage.enter_email)
        await state.update_data(mode_type=mode_type, days=days, amount=amount)
        await call.message.answer("Для проведения оплаты нам понадобиться адрес электронной почты,"
                                  " чтобы направить чек о покупке 🧾\n\nПожалуйста, введи свой email 🍏",
                                  reply_markup=menu_keyboard.as_markup())
    else:
        await send_invoice(user.user_id, amount, days, mode_type)
    await call.message.delete()


@payment_router.message(F.text, InputMessage.enter_email)
async def enter_user_email(message: types.Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    mode_type = state_data.get("mode_type")
    if await is_valid_email(email=message.text):
        await state.clear()
        await message.answer("Отлично, мы сохранили твой email для следующих покупок")
        await users_repository.update_email_by_user_id(user_id=message.from_user.id, email=message.text)
        await send_invoice(
            user_id=message.from_user.id,
            amount=state_data.get("amount"),
            days=state_data.get("days"),
            mode_type=mode_type
        )
    else:
        await message.answer("Введенный тобой email некорректен, попробуй еще раз",
                                           reply_markup=cancel_keyboard.as_markup())


@payment_router.callback_query(F.data.startswith("is_paid|"), any_state)
async def check_payment_callback(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = call.data.split("|")
    operation_id = data[1]
    days = int(data[2])
    mode_type = data[3]

    user_id = call.from_user.id
    operation = await operation_repository.get_operation_info_by_id(int(operation_id))
    payment_id = operation.operation_id
    if await check_payment(payment_id):
        payment_method_id = await get_payment_method_id(payment_id)
        user_payment_method_id = await payment_methods_repository.get_payment_method_by_user_id(user_id)
        if not user_payment_method_id:
            await payment_methods_repository.add_payment_method(user_id, payment_method_id)
        else:
            await payment_methods_repository.update_payment_method_by_user_id(user_id, payment_method_id)

        await operation_repository.update_paid_by_operation_id(payment_id)
        date_now = datetime.datetime.now(timezone.utc)
        if mode_type == "gift":
            promo_code = await generate_single_promo_code()
            await referral_system_repository.add_promo(promo_code=promo_code,
                                                       max_days=days,
                                                       max_activations=1,
                                                       type_promo="from_admin")
            link = await create_start_link(call.bot, promo_code)
            await call.message.answer(
                f"Отлично, этот промокод даёт подписку на {days} дней: <code>{promo_code}</code>. Твоему другу достаточно"
                f" ввести этот промокод, либо нажать на ссылку: {link}, чтобы получить свои бонусы твой подарок!",
                reply_markup=menu_keyboard.as_markup())
        else:
            user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
            if user_sub is None:
                await subscriptions_repository.add_subscription(user_id=user_id,
                                                                time_limit_subscription=days,
                                                                active=True,
                                                                recurrent=True,
                                                                plan=days)
                await subscribed_callback(user_id, days)
            else:
                last_sub_date_end = user_sub.creation_date + datetime.timedelta(days=user_sub.time_limit_subscription)
                difference = last_sub_date_end - date_now
                await subscriptions_repository.deactivate_subscription(subscription_id=user_sub.id)
                await subscriptions_repository.add_subscription(user_id=user_id,
                                                                time_limit_subscription=days + difference.days,
                                                                recurrent=True,
                                                                plan=days)

                await send_prolong_subscription_message(user_id, days, user_sub.id)

            await call.message.delete()

    else:
        try:
            payment = await operation_repository.get_operation_by_operation_id(payment_id)
            keyboard = await keyboard_for_pay(operation_id=operation_id, url=payment.url,
                                              time_limit=30, mode_type=mode_type)
            await call.message.edit_text("Пока мы не видим, чтобы оплата была произведена( Погоди"
                                            " еще немного времени и убедись,"
                                            " что ты действительно произвел оплату(",
                                         reply_markup=keyboard.as_markup())
        finally:
            return
