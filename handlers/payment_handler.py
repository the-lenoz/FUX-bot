import datetime

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state

from bots import main_bot
from data.keyboards import cancel_keyboard, menu_keyboard, keyboard_for_pay, generate_sub_keyboard
from db.repository import users_repository, subscriptions_repository, operation_repository, recommendations_repository
from settings import InputMessage, is_valid_email, sub_description_photo, you_fooher_photo, \
    sub_description_photo2
from utils.checkup_stat import send_weekly_checkup_report
from utils.gpt_client import LLMProvider
from utils.gpt_distributor import user_request_handler
from utils.payment_for_services import create_payment, check_payment

payment_router = Router()


@payment_router.callback_query(F.data.startswith("subscribe"), any_state)
async def subscribe(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    user = await users_repository.get_user_by_user_id(call.from_user.id)
    call_data = call.data.split("|")
    if len(call_data) > 1:
        mode_type = call_data[1]
    else:
        mode_type = None
    sub = await subscriptions_repository.get_active_subscription_by_user_id(user.user_id)
    # if sub:
    #     await call.message.answer("На данный момент у тебя уже есть подписка",
    #                               reply_markup=menu_keyboard.as_markup())
    if user.email is None:
        await state.set_state(InputMessage.enter_email)
        await state.update_data(mode_type=mode_type)
        await call.message.answer("Для проведения оплаты нам понадобиться адрес электронной почты,"
                                  " чтобы направить чек о покупке 🧾\n\nПожалуйста, введи свой email 🍏",
                                  reply_markup=menu_keyboard.as_markup())
        try:
            await call.message.delete()
        finally:
            return
    await call.message.answer_photo(photo=sub_description_photo,
                                    reply_markup=generate_sub_keyboard(mode_type=mode_type).as_markup())
    try:
        await call.message.delete()
    finally:
        return


@payment_router.callback_query(F.data.startswith("choice_sub"), any_state)
async def get_choice_of_sub(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    call_data = call.data.split("|")
    days, amount, mode_type = call_data[1], call_data[2], call_data[3]
    user = await users_repository.get_user_by_user_id(call.from_user.id)
    if user.email is None:
        await state.set_state(InputMessage.enter_email)
        await state.update_data(mode_type=mode_type)
        await call.message.answer("Для проведения оплаты нам понадобиться адрес электронной почты,"
                                  " чтобы направить чек о покупке 🧾\n\nПожалуйста, введи свой email 🍏",
                                  reply_markup=menu_keyboard.as_markup())
        try:
            await call.message.delete()
        finally:
            return
    payment = await create_payment(user.email, amount=amount)
    await operation_repository.add_operation(operation_id=payment[0], user_id=call.from_user.id, is_paid=False,
                                             url=payment[1])
    operation = await operation_repository.get_operation_by_operation_id(payment[0])
    keyboard = await keyboard_for_pay(operation_id=operation.id, url=payment[1],
                                      time_limit=int(days), mode_type=mode_type)
    await call.message.answer(text=f'Для дальнейшей работы ассистента нужно приобрести подписку'
                                   f' за {amount[:-3]} рублей.\n\nПосле проведения платежа нажми на кнопку "Оплата произведена",'
                                   ' чтобы подтвердить платеж', reply_markup=keyboard.as_markup())
    try:
        await call.message.delete()
    finally:
        return


@payment_router.message(F.text, InputMessage.enter_email)
async def enter_user_email(message: types.Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    mode_type = state_data.get("mode_type")
    if await is_valid_email(email=message.text):
        await state.clear()
        await message.answer("Отлично, мы сохранили твой email для следующих покупок")
        await users_repository.update_email_by_user_id(user_id=message.from_user.id, email=message.text)
        await message.answer_photo(photo=sub_description_photo,
                                   reply_markup=generate_sub_keyboard(mode_type=mode_type).as_markup())
    else:
        del_message = await message.answer("Введеный тобой email некорректен, попробуй еще раз",
                                           reply_markup=cancel_keyboard.as_markup())


@payment_router.callback_query(F.data.startswith("is_paid|"), any_state)
async def check_payment_callback(message: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = message.data.split("|")
    operation_id = data[1]
    days = int(data[2])
    mode_type = data[3]

    user_id = message.from_user.id
    operation = await operation_repository.get_operation_info_by_id(int(operation_id))
    payment_id = operation.operation_id
    if await check_payment(payment_id) or True: # TODO - remove TEST
        await operation_repository.update_paid_by_operation_id(payment_id)
        date_now = datetime.datetime.now()
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        date_end = datetime.datetime.now() + datetime.timedelta(days=days)
        if user_sub is None:
            await subscriptions_repository.add_subscription(user_id=user_id,
                                                            time_limit_subscription=days,
                                                            active=True)
        else:
            # await subscriptions_repository.update_time_limit_subscription(subscription_id=user_sub.id,
            #                                                               new_time_limit=days)
            last_sub_date_end = user_sub.creation_date + datetime.timedelta(days=user_sub.time_limit_subscription)
            difference = last_sub_date_end - date_now
            await subscriptions_repository.deactivate_subscription(subscription_id=user_sub.id)
            await subscriptions_repository.add_subscription(user_id=user_id,
                                                            time_limit_subscription=days + difference.days,)
            date_end = date_end + datetime.timedelta(days=user_sub.time_limit_subscription)
        await message.message.delete()

        formatted_date = date_end.strftime('%d.%m.%y, %H:%M')
        await message.message.answer_photo(photo=you_fooher_photo)

        await message.message.answer_photo(
            photo=sub_description_photo2,
            caption=f"Поздравляю! Твоя подписка активна до {formatted_date} +GMT3",
            reply_markup=menu_keyboard.as_markup()
        )
        if mode_type.startswith("recommendation"):
            recommendation_id = int(mode_type.split('-')[1])
            recommendation = await recommendations_repository.get_recommendation_by_recommendation_id(
                recommendation_id=recommendation_id
            )
            await user_request_handler.AI_handler.send_recommendation(
                user_id=user_id,
                recommendation=recommendation.text,
                problem_id=recommendation.problem_id,
                from_notification=False
            )
        elif mode_type.startswith("tracking"):
            date = datetime.datetime.fromtimestamp(int(mode_type.split('-')[1]))
            await send_weekly_checkup_report(user_id, date)
    else:
        try:
            payment = await operation_repository.get_operation_by_operation_id(payment_id)
            keyboard = await keyboard_for_pay(operation_id=operation_id, url=payment.url,
                                              time_limit=30, mode_type=mode_type)
            await message.message.edit_text("Пока мы не видим, чтобы оплата была произведена( Погоди"
                                            " еще немного времени и убедись,"
                                            " что ты действительно произвел оплату(",
                                            reply_markup=keyboard.as_markup())
        finally:
            return