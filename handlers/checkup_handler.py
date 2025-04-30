from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.keyboards import checkup_type_keyboard, buy_sub_keyboard, menu_keyboard, menu_button, \
    emotions_keyboard, productivity_keyboard, delete_checkups_keyboard
from db.repository import users_repository, subscriptions_repository, checkup_repository, days_checkups_repository
from settings import mechanic_checkup, InputMessage, is_valid_time, checkup_emotions_photo, checkup_productivity_photo, \
    checkups_types_photo
from utils.сheckup_stat import generate_emotion_chart

checkup_router = Router()


@checkup_router.callback_query(F.data == "go_checkup")
async def go_checkup(call: CallbackQuery):
    user_id = call.from_user.id
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    keyboard = InlineKeyboardBuilder()
    have_checkups = False
    for checkup in user_checkups:
        active_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
        if active_day:
            have_checkups = True
            button_text = "🤩Трекинг эмоций" if checkup.type_checkup == "emotions" else "🚀Трекинг продуктивности"
            keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"start_checkup|"
                                                                              f"{checkup.id}|"
                                                                              f"{active_day.id}"
                                                                              f"|{checkup.type_checkup}|"))
    keyboard.row(menu_button)
    message_text = "Выбери трекинг, который хочешь пройти"
    if not have_checkups:
        message_text = "На данный момент у тебя нет трекингов, которые можно пройти"
    await call.message.answer(message_text, reply_markup=keyboard.as_markup())
    await call.message.delete()


@checkup_router.callback_query(F.data.startswith("start_checkup|"), any_state)
async def get_checkup_question(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    call_data = call.data.split("|")
    checkup_id, day_checkup_id, type_checkup = call_data[1], call_data[2], call_data[3]
    message_photo = checkup_emotions_photo
    check_data = "|".join(call_data[1:])
    keyboard = emotions_keyboard(check_data)
    if type_checkup == "productivity":
        message_photo = checkup_productivity_photo
        keyboard = productivity_keyboard(check_data)
    await call.message.answer_photo(photo=message_photo,
                                    reply_markup=keyboard.as_markup())
    await checkup_repository.update_last_date_send_checkup_by_checkup_id(checkup_id=int(checkup_id),
                                                                         last_date_send=datetime.now())
    await call.message.delete()


@checkup_router.callback_query(F.data.startswith("enter_emoji|"), any_state)
async def enter_emoji_user(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user_active_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    now_date = datetime.now()
    update_power_mode = False
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user_active_checkups is not None and len(user_active_checkups) > 0:
        max_date = None
        for checkup in user_active_checkups:
            last_ended_day = await days_checkups_repository.get_latest_ended_day_checkup_by_checkup_id(
                checkup_id=checkup.id)
            if last_ended_day is not None and (max_date is None or last_ended_day.date_end_day.date() > max_date):
                max_date = last_ended_day.date_end_day.date()
        if max_date is None or (now_date.date() != max_date):
            await users_repository.update_power_mode_days_by_user_id(user_id=user_id, new_days=user.power_mode_days + 1)
            update_power_mode = True
    call_data = call.data.split("|")[1:]
    emoji, checkup_id, day_checkup_id, type_checkup = (int(call_data[0]), int(call_data[1]),
                                                       int(call_data[2]), call_data[3])
    day_checkup = await days_checkups_repository.get_day_checkup_by_day_checkup_id(day_checkup_id=day_checkup_id)
    await days_checkups_repository.update_data_by_day_checkup_id(day_checkup_id=day_checkup_id,
                                                                 points=emoji)
    await call.message.answer("Спасибо за ответ!")
    if day_checkup.day >= 7:
        checkup_days = await days_checkups_repository.get_days_checkups_by_checkup_id(checkup_id=checkup_id)
        # graphic = generate_emotion_chart(emotion_data=[day.points for day in checkup_days], dates=[day.date_end_day for day in checkup_days])
        graphic = generate_emotion_chart(emotion_data=[checkup_day.points for checkup_day in checkup_days],
                                         dates=[checkup_day.date_end_day.strftime("%d-%m") for checkup_day in checkup_days],
                                         checkup_type=type_checkup)
        graphic_bytes = graphic.getvalue()
        # Отправка голосового сообщения
        await call.message.answer_photo(
            photo=BufferedInputFile(file=graphic_bytes, filename="graphic.png"),
            caption="Итоговый результат пройденного тобой трекинга",
            reply_markup=menu_keyboard.as_markup()
        )
        await checkup_repository.update_ending_by_checkup_id(checkup_id=checkup_id)
    if update_power_mode:
        await call.message.answer(f"{user.power_mode_days + 1} орех подряд!🌰 Продолжай с трекингом в том же духе")
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
    if user_checkup is None:
        await call.message.answer("Для того, чтобы продолжить, введи, пожалуйста время в которое, тебе отправлять"
                                  " трекинг. Пример: 14:45",
                                  reply_markup=menu_keyboard.as_markup())
        await state.set_state(InputMessage.enter_time_checkup)
        await state.update_data(type_checkup=type_checkup)
        await call.message.delete()
        return
    await call.message.delete()
    await call.message.answer("Этот формат трекинга уже активен🧡",
                              reply_markup=delete_checkups_keyboard(type_checkup=type_checkup,
                                                                    checkup_id=user_checkup.id).as_markup())


@checkup_router.callback_query(F.data.startswith("delete_checkups|"), any_state)
async def delete_checkups(call: CallbackQuery, state: FSMContext):
    call_data = call.data.split("|")[1:]
    type_checkup = call_data[0]
    checkup_id = int(call_data[1])
    await checkup_repository.delete_checkup_by_checkup_id(checkup_id=checkup_id)
    await call.message.answer("⚙Трекинг состояния отключён! Теперь тебе не будут приходить уведомления.\n\n"
                              "Если захочешь включить его снова, то это всегда можно будет сделать"
                              " в разделе «<b>🗓Трекинг состояния</b>»")
    await call.message.delete()



@checkup_router.message(F.text, InputMessage.enter_time_checkup)
async def update_tine_checkup(message: Message, state: FSMContext):
    user_id = message.from_user.id
    result = is_valid_time(message.text)
    state_data = await state.get_data()
    await state.clear()
    type_checkup = state_data.get("type_checkup")
    user_checkups = await checkup_repository.get_checkups_by_user_id(user_id=user_id)
    if result:
        time_obj = datetime.strptime(message.text, "%H:%M").time()
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
        await days_checkups_repository. add_day_checkup(checkup_id=user_checkup.id,
                                                       day=1,
                                                       points=0)
        await message.answer('🐿️Отлично, теперь в это время тебе будет приходить ежедневный трекинг.\n\n'
                             'Если ты захочешь пройти трекинг в другое время,'
                             ' то ты всегда сможешь изменить его в настройках⚙️',
                             reply_markup=menu_keyboard.as_markup())
    else:
        await state.set_state(InputMessage.enter_time_checkup)
        await state.update_data(type_checkup=type_checkup)
        await message.answer("Введенное тобой время имеет неправильный формат. Пример - 13:45. Попробуй еще раз",
                             reply_markup=menu_keyboard.as_markup())

