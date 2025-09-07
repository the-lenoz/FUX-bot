from datetime import datetime, timezone

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots import main_bot
from data.keyboards import menu_keyboard, menu_button, get_ai_temperature_keyboard, menu_age_keyboard, \
    settings_cancel_keyboard, choice_gender_settings_keyboard
from db.repository import users_repository, checkup_repository, subscriptions_repository, user_timezone_repository
from settings import DEFAULT_TIMEZONE
from data.message_templates import messages_dict
from data.images import temperature_ai_photo, checkup_emotions_photo, checkup_productivity_photo
from utils.state_models import InputMessage, AccountSettingsStates
from utils.gpt_distributor import user_request_handler
from utils.timezone_matcher import calculate_timezone
from utils.account_manager import delete_user
from utils.validators import is_valid_email, is_valid_time

system_settings_router = Router()


@system_settings_router.message(Command("settings"))
async def settings_command_handler(message: Message, bot: Bot):
    await send_system_settings(message.from_user.id)


@system_settings_router.callback_query(F.data == "system_settings", any_state)
async def system_settings_callback(call: CallbackQuery, state: FSMContext):
    await send_system_settings(call.from_user.id)
    await call.message.delete()


async def send_system_settings(user_id: int):
    await user_request_handler.AI_handler.exit(user_id)
    keyboard = InlineKeyboardBuilder()
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    user = await users_repository.get_user_by_user_id(user_id)
    timezone_delta = await user_timezone_repository.get_user_timezone_delta(user_id)
    user_timezone_name = calculate_timezone(datetime.now(timezone(timezone_delta)))[0] if timezone_delta else None

    keyboard.row(
        InlineKeyboardButton(text=f"Имя: {user.name if user.name else 'НЕ УСТАНОВЛЕНО'}",
                             callback_data="settings|edit|name")
    )
    keyboard.row(
        InlineKeyboardButton(text=f"Возраст: {user.age if user.age else 'НЕ УСТАНОВЛЕН'}",
                             callback_data="settings|edit|age")
    )
    keyboard.row(
        InlineKeyboardButton(text=f"Пол: {'Мужской' if user.gender == 'male' else ('Женский' if user.gender == 'female' else 'НЕ УСТАНОВЛЕН')}",
                             callback_data="settings|edit|gender")
    )
    keyboard.row(InlineKeyboardButton(text=f"👄Режим общения: {'Прямолинейный' if user.ai_temperature == 0.6 else 'Нейтральный'}", callback_data="settings|temperature"))
    keyboard.row(
        InlineKeyboardButton(
            text=f"Часовой пояс: {user_timezone_name[:8] if user_timezone_name else 'НЕ УСТАНОВЛЕН'}",
            callback_data="settings|edit|timezone")
    )
    if user.email:
        keyboard.row(InlineKeyboardButton(text=f"Email: {user.email}", callback_data="settings|edit|email"))
    for checkup in user_checkups:
        text = ("Время трекинга эмоций🤩" if checkup.type_checkup == "emotions" else "Время трекинга продуктивности🚀") + f": {(datetime.combine(datetime.today(), checkup.time_checkup) + timezone_delta).time().strftime('%H:%M')}"
        keyboard.row(InlineKeyboardButton(text=text, callback_data=f"edit_checkup|{checkup.id}"))
    keyboard.row(InlineKeyboardButton(text="🗑 Удалить все данные", callback_data=f"delete_account|0"))
    keyboard.row(menu_button)
    await main_bot.send_message(chat_id=user_id,
                                text="Здесь ты можешь <b>менять</b> <u>настройки</u>",
                                reply_markup=keyboard.as_markup())

@system_settings_router.callback_query(F.data.startswith("settings|edit"), any_state)
async def edit_profile(call: CallbackQuery, state: FSMContext):
    edit_type = call.data.split('|')[-1]
    if edit_type == 'name':
        await call.message.answer(
            "Введи своё имя:",
            reply_markup=settings_cancel_keyboard.as_markup()
        )
        await state.set_state(AccountSettingsStates.edit_name)
    elif edit_type == 'email':
        await call.message.answer(
            "Введи новый email:",
            reply_markup=settings_cancel_keyboard.as_markup()
        )
        await state.set_state(AccountSettingsStates.edit_email)
    elif edit_type == 'age':
        await call.message.answer("Какой возрастной диапазон тебе ближе?",
                                  reply_markup=menu_age_keyboard.as_markup())
        await state.set_state(AccountSettingsStates.edit_age)
    elif edit_type == 'gender':
        await call.message.answer("В каком роде мне к тебе обращаться?",
                             reply_markup=choice_gender_settings_keyboard.as_markup())
        await state.set_state(AccountSettingsStates.edit_gender)
    elif edit_type == 'timezone':
        await call.message.answer(messages_dict["timezone_input_message_text"],
                                  reply_markup=settings_cancel_keyboard.as_markup())
        await state.set_state(InputMessage.enter_timezone)

    await call.message.delete()

@system_settings_router.message(F.text, AccountSettingsStates.edit_name)
async def edit_account_name(message: Message, state: FSMContext, bot: Bot):
    name = message.text.strip()
    await users_repository.update_initials_id_by_user_id(
        user_id=message.from_user.id,
        first_name=name
    )
    await state.clear()

    await message.answer(
        "Имя сохранено!",
        reply_markup=settings_cancel_keyboard.as_markup()
    )

@system_settings_router.message(F.text, AccountSettingsStates.edit_email)
async def edit_account_email(message: Message, state: FSMContext, bot: Bot):
    email = message.text.strip()
    if await is_valid_email(email):
        await users_repository.update_email_by_user_id(
            user_id=message.from_user.id,
            email=email
        )
        await state.clear()

        await message.answer(
            "Новый email сохранён!",
            reply_markup=settings_cancel_keyboard.as_markup()
        )
    else:
        await message.answer(
            "Email некорректен, попробуй ещё раз:"
        )

@system_settings_router.callback_query(F.data.startswith("settings|checkups"), any_state)
async def set_system_settings_checkups(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await user_request_handler.AI_handler.exit(user_id)
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    keyboard = InlineKeyboardBuilder()
    for checkup in user_checkups:
        text = "🤩Трекинг эмоций" if checkup.type_checkup == "emotions" else "🚀Трекинг продуктивности"
        keyboard.row(InlineKeyboardButton(text=text, callback_data=f"edit_checkup|{checkup.id}"))
    keyboard.row(menu_button)
    await call.message.answer("Выбери трекинг, время которого, ты хочешь изменить⚙️",
                              reply_markup=keyboard.as_markup())
    await call.message.delete()

@system_settings_router.callback_query(F.data.startswith("settings|temperature"), any_state)
async def set_system_settings_temperature(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    user = await users_repository.get_user_by_user_id(user_id)
    if user_sub:
        await call.message.answer_photo(photo=temperature_ai_photo,
                                        caption=messages_dict["communication_mode_mechanic_text"], reply_markup=get_ai_temperature_keyboard(user.ai_temperature).as_markup())
        await call.message.delete()
    else:
        await call.message.answer("К сожалению, ты не можешь изменить "
                                  "режим общения, так как у тебя нет подписки 🌰",
                                  reply_markup=menu_keyboard.as_markup())
        await call.message.delete()



@system_settings_router.callback_query(F.data.startswith("ai_temperature"), any_state)
async def ai_temperature_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await user_request_handler.AI_handler.exit(user_id)
    ai_temperature = float(call.data.split("|")[1])
    await users_repository.update_ai_temperature_by_user_id(user_id, ai_temperature)
    await call.message.answer("Отлично, настройки твоего ассистента изменены!")
    await call.message.delete()
    await send_system_settings(user_id)



@system_settings_router.callback_query(F.data.startswith("edit_checkup"), any_state)
async def edit_checkup_time_call(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await user_request_handler.AI_handler.exit(user_id)
    checkup_id = int(call.data.split("|")[1])
    checkup = await checkup_repository.get_checkup_by_checkup_id(checkup_id=checkup_id)
    await state.set_state(InputMessage.edit_time_checkup)
    await state.update_data(checkup_id=checkup_id)
    timezone_delta = await user_timezone_repository.get_user_timezone_delta(user_id) or DEFAULT_TIMEZONE
    await call.message.answer_photo(photo=checkup_emotions_photo if checkup.type_checkup == "emotions" else checkup_productivity_photo,
                                        caption="Для того, чтобы продолжить, введи, пожалуйста, время, в которое тебе отправлять <u>трекинг</u> " + ("<b>эмоций</b>" if checkup.type_checkup == "emotions" else "<b>продуктивности</b>") +
                              f"\n\nСейчас данный трекинг отправляется в {(datetime.combine(datetime.today(), checkup.time_checkup) + timezone_delta).time().strftime('%H:%M')}",
                              reply_markup=settings_cancel_keyboard.as_markup())
    await call.message.delete()



@system_settings_router.message(F.text, InputMessage.edit_time_checkup)
async def enter_new_checkup_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await user_request_handler.AI_handler.exit(user_id)
    state_data = await state.get_data()
    await state.clear()
    checkup_id = int(state_data.get("checkup_id"))
    if is_valid_time(message.text):
        user_timezone_delta = await user_timezone_repository.get_user_timezone_delta(user_id) or DEFAULT_TIMEZONE
        time = (datetime.strptime(message.text, "%H:%M") - user_timezone_delta).time()
        await checkup_repository.update_time_checkup_by_checkup_id(checkup_id=checkup_id,
                                                                   time_checkup=time)
        await message.answer(f"Отлично, теперь данный трекинг будет отправляться в {message.text}",
                             reply_markup=menu_keyboard.as_markup())
        return
    await state.set_state(InputMessage.edit_time_checkup)
    await state.update_data(checkup_id=checkup_id)
    await message.answer("Введенное тобой время имеет неправильный формат. Пример - 13:45. Попробуй еще раз",
                         reply_markup=menu_keyboard.as_markup())



@system_settings_router.callback_query(F.data.startswith("delete_account"), any_state) # DO NOT USE
async def delete_account(call: CallbackQuery, state: FSMContext):
    confirm = int(call.data.split('|')[-1])
    if confirm:
        await delete_user(call.from_user.id)
        await call.message.answer("Ты удалил всю информацию, теперь я ничего про тебя не помню.\nЧтобы начать общение, нажми /start")
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="system_settings"))
        keyboard.row(InlineKeyboardButton(text="Да, удалить", callback_data="delete_account|1"))
        await call.message.answer(
            "Ты точно хочешь всё удалить? (это безвозвратно!)",
            reply_markup=keyboard.as_markup()
        )