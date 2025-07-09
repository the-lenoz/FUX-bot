from asyncio import Lock
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import utils.checkups
from data.keyboards import checkup_type_keyboard, buy_sub_keyboard, menu_keyboard, menu_button, \
    delete_checkups_keyboard
from db.repository import users_repository, subscriptions_repository, checkup_repository, days_checkups_repository, \
    user_timezone_repository
from settings import mechanic_checkup, InputMessage, is_valid_time, checkups_types_photo, checkup_emotions_photo, \
    checkup_productivity_photo
from utils.checkups_ended import sent_today
from utils.checkup_stat import send_weekly_checkup_report, send_monthly_checkup_report
from utils.timezone_matcher import calculate_timezone

checkup_router = Router()


user_checkup_locks = {}


@checkup_router.callback_query(F.data == "go_checkup")
async def go_checkup(call: CallbackQuery):
    user_id = call.from_user.id
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    keyboard = InlineKeyboardBuilder()
    have_checkups = False
    for checkup in user_checkups:
        active_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
        if active_day or (datetime.now().time() < checkup.time_checkup and not await sent_today(checkup.id)):
            have_checkups = True
            button_text = "🤩Трекинг эмоций" if checkup.type_checkup == "emotions" else "🚀Трекинг продуктивности"
            keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"start_checkup|{checkup.id}"))
    keyboard.row(menu_button)
    message_text = "Выбери трекинг, который хочешь пройти"
    if not have_checkups:
        message_text = "На данный момент у тебя нет трекингов, которые можно пройти"
    await call.message.answer(message_text, reply_markup=keyboard.as_markup())
    await call.message.delete()


@checkup_router.callback_query(F.data.startswith("start_checkup|"), any_state)
async def get_checkup_question(call: CallbackQuery, state: FSMContext):
    call_data = call.data.split("|")
    checkup_id = int(call_data[1])
    await utils.checkups.send_checkup(checkup_id)
    await call.message.delete()


@checkup_router.callback_query(F.data.startswith("enter_emoji|"), any_state)
async def enter_emoji_user(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if not user_checkup_locks.get(user_id):
        user_checkup_locks[user_id] = Lock()
    async with user_checkup_locks[user_id]:
        update_power_mode = True
        user = await users_repository.get_user_by_user_id(user_id=user_id)
        call_data = call.data.split("|")[1:]
        emoji, checkup_id, day_checkup_id, type_checkup = (int(call_data[0]), int(call_data[1]),
                                                           int(call_data[2]), call_data[3])
        day_checkup = await days_checkups_repository.get_day_checkup_by_day_checkup_id(day_checkup_id=day_checkup_id)
        await days_checkups_repository.update_data_by_day_checkup_id(day_checkup_id=day_checkup_id,
                                                                     points=emoji)
        user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id)
        for checkup in user_checkups:
            checkup_days = await days_checkups_repository.get_days_checkups_by_checkup_id(checkup.id)
            checkup_sent_in_call_checkup_day = False
            for checkup_day_data in checkup_days:
                if checkup_day_data.creation_date.date() == day_checkup.creation_date.date():
                    checkup_sent_in_call_checkup_day = True
                    if not checkup_day_data.date_end_day:
                        update_power_mode = False
            if not checkup_sent_in_call_checkup_day:
                update_power_mode = False


        await call.message.answer("Спасибо за ответ!", reply_markup=menu_keyboard.as_markup()   )
        if update_power_mode:
            if day_checkup.creation_date.weekday() == 6:
                await send_weekly_checkup_report(user.user_id, day_checkup.creation_date)
            if (day_checkup.creation_date + timedelta(days=1)).month != day_checkup.creation_date.month:
                    await send_monthly_checkup_report(user.user_id, day_checkup.creation_date)

            await users_repository.update_power_mode_days_by_user_id(user_id, user.power_mode_days + 1)
            await call.message.answer(f"{user.power_mode_days + 1} орех подряд!🌰 Продолжай с трекингом в том же духе")


        if type_checkup == "emotions":
            await users_repository.user_tracked_emotions(user_id)
        elif type_checkup == "productivity":
            await users_repository.user_tracked_productivity(user_id)

        await call.message.delete()


@checkup_router.callback_query(F.data == "checkups", any_state)
async def start_checkup(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer_photo(photo=checkups_types_photo,
                                    caption=mechanic_checkup, reply_markup=checkup_type_keyboard.as_markup())


@checkup_router.callback_query(F.data.startswith("checkups|"), any_state)
async def start_checkups(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    type_checkup = call.data.split("|")[1]
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    user_checkups = await checkup_repository.get_checkups_by_user_id(user_id=user_id)
    if user_sub is None and (user_checkups is not None) and len(user_checkups) >= 1:
        await call.message.answer("🌰️Для этого нужно расколоть орех…",
                             reply_markup=buy_sub_keyboard.as_markup())
        await call.message.delete()
        return
    user_checkup = await checkup_repository.get_active_checkup_by_user_id_type_checkup(user_id=user_id,
                                                                                       type_checkup=type_checkup)
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    await state.update_data(type_checkup=type_checkup)
    if user_checkup is None:
        if not await user_timezone_repository.get_user_timezone_delta(user_id):
            await call.message.answer("🕒 Хочу быть в твоём ритме. Пришли своё текущее время (в формате 24ч), чтобы я определил часовой пояс. Пример: 18:12")
            await state.set_state(InputMessage.enter_timezone)
            await state.update_data(enter_checkup_time=True)
        else:
            await call.message.answer_photo(
                photo=checkup_emotions_photo if type_checkup == "emotions" else checkup_productivity_photo,
                caption="Для того, чтобы продолжить, введи, пожалуйста время в которое, тебе отправлять"
                        " <u>трекинг</u> " + (
                            "<b>эмоций</b>" if type_checkup == "emotions" else "<b>продуктивности</b>") + ". Пример: 21:00",
                reply_markup=menu_keyboard.as_markup())
            await state.set_state(InputMessage.enter_time_checkup)
        await call.message.delete()
        return
    await call.message.delete()
    await call.message.answer("Этот формат трекинга уже активен🧡",
                              reply_markup=delete_checkups_keyboard(type_checkup=type_checkup,
                                                                    checkup_id=user_checkup.id).as_markup())


@checkup_router.callback_query(F.data.startswith("delete_checkups|"), any_state)
async def delete_checkups(call: CallbackQuery, state: FSMContext):
    call_data = call.data.split("|")[1:]
    checkup_id = int(call_data[1])
    await checkup_repository.delete_checkup_by_checkup_id(checkup_id=checkup_id)
    await call.message.answer("⚙Трекинг состояния отключён! Теперь тебе не будут приходить уведомления.\n\n"
                              "Если захочешь включить его снова, то это всегда можно будет сделать"
                              " в разделе «<b>🗓Трекинг состояния</b>»")
    await call.message.delete()


@checkup_router.message(F.text, InputMessage.enter_timezone)
async def set_user_timezone(message: Message, state: FSMContext):
    try:
        time = datetime.strptime(message.text, "%H:%M")
    except ValueError:
        await message.answer(
            "Неверный формат времени, попробуй ещё раз!")
        await state.set_state(InputMessage.enter_timezone)
        return

    timezone = calculate_timezone(time)
    await message.answer(f"<b>Часовой пояс</b> успешно <u>установлен</u>: {timezone[0]}")
    await user_timezone_repository.set_user_timezone_delta(user_id=message.from_user.id,
                                                           timezone_utc_delta=timezone[1])

    type_checkup = state.get_value("type_checkup")

    if state.get_value("enter_checkup_time"):
        await message.answer_photo(
            photo=checkup_emotions_photo if type_checkup == "emotions" else checkup_productivity_photo,
            caption="Для того, чтобы продолжить, введи, пожалуйста время в которое, тебе отправлять"
                    " <u>трекинг</u> " + (
                        "<b>эмоций</b>" if type_checkup == "emotions" else "<b>продуктивности</b>") + ". Пример: 21:00",
            reply_markup=menu_keyboard.as_markup())
        await state.set_state(InputMessage.enter_time_checkup)



@checkup_router.message(F.text, InputMessage.enter_time_checkup)
async def update_tine_checkup(message: Message, state: FSMContext):
    user_id = message.from_user.id
    result = is_valid_time(message.text)
    state_data = await state.get_data()
    await state.clear()
    type_checkup = state_data.get("type_checkup")
    user_checkups = await checkup_repository.get_checkups_by_user_id(user_id=user_id)
    user_timezone_delta = await user_timezone_repository.get_user_timezone_delta(user_id)
    if result:
        time_obj = (datetime.strptime(message.text, "%H:%M") + user_timezone_delta).time()

        if user_checkups is None or len(user_checkups) == 0:
            number_checkup = 0
        else:
            number_checkup = len(user_checkups)
        await checkup_repository.add_checkup(user_id=user_id,
                                             type_checkup=type_checkup,
                                             number_checkup=number_checkup + 1,
                                             time_checkup=time_obj)
        user_checkup = await checkup_repository.get_active_checkup_by_user_id_type_checkup(user_id=user_id,
                                                                                            type_checkup=type_checkup)
        await days_checkups_repository.add_day_checkup(checkup_id=user_checkup.id,
                                                       day=1,
                                                       points=0,
                                                       user_id=user_id,
                                                       checkup_type=type_checkup)
        await message.answer('🐿️Отлично, теперь в это время тебе будет приходить ежедневный трекинг.\n\n'
                             'Если ты захочешь пройти трекинг в другое время,'
                             ' то ты всегда сможешь изменить его в настройках⚙️',
                             reply_markup=menu_keyboard.as_markup())
    else:
        await state.set_state(InputMessage.enter_time_checkup)
        await state.update_data(type_checkup=type_checkup)
        await message.answer("Введенное тобой время имеет неправильный формат. Пример - 13:45. Попробуй еще раз",
                             reply_markup=menu_keyboard.as_markup())

