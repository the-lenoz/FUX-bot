from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.keyboards import  menu_keyboard, menu_button, ai_temperature_keyboard
from db.repository import users_repository, checkup_repository, subscriptions_repository
from settings import InputMessage, mechanic_text, mechanic_checkup, is_valid_email, fast_help_promt, go_deeper_promt, \
    ai_temperature_text, is_valid_time, temperature_ai_photo

system_settings_router = Router()


@system_settings_router.callback_query(F.data == "system_settings", any_state)
async def system_settings_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    keyboard = InlineKeyboardBuilder()
    user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
    if user_checkups:
        keyboard.row(InlineKeyboardButton(text="Настройка трекингов", callback_data="settings|checkups"))
    keyboard.row(InlineKeyboardButton(text="Формат общения", callback_data="settings|temperature"))
    keyboard.row(menu_button)
    await call.message.answer("Я также умею <b>говорить прямо</b> — без сюсюканья и лишней мягкости.🎯\n\n"
                              "Если тебе комфортнее, когда с тобой говорят по делу, чётко и без обёрток — просто"
                              " включи прямолинейный режим.\n\nПример, как я не буду:\n\n“Ты справляешься, даже если чувствуешь усталость. "
                              "Всё ок, просто постарайся немного замедлиться.”\n\n🐿️Пример, как я буду:\n\n“Ты выгорел,"
                              " потому что сам себя загнал. Отдохни уже, а не героически страдай.”\n\n"
                              "🌰доступно только в платной версии.",
                              reply_markup=keyboard.as_markup())
    await call.message.delete()


@system_settings_router.callback_query(F.data.startswith("settings"), any_state)
async def set_system_settings(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    type_setting = call.data.split("|")[1]
    if type_setting == "checkups":
        user_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user_id)
        keyboard = InlineKeyboardBuilder()
        for checkup in user_checkups:
            text = "🤩Трекинг эмоций" if checkup.type_checkup == "emotions" else "🚀Трекинг продуктивности"
            keyboard.row(InlineKeyboardButton(text=text, callback_data=f"edit_checkup|{checkup.id}"))
        keyboard.row(menu_button)
        await call.message.answer("Выбери трекинг, время которого, ты хочешь изменить⚙️",
                                  reply_markup=keyboard.as_markup())
        await call.message.delete()
        return
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    if user_sub:
        await call.message.answer_photo(photo=temperature_ai_photo,
                                        caption=ai_temperature_text, reply_markup=ai_temperature_keyboard.as_markup())
        await call.message.delete()
    else:
        await call.message.answer("К сожалению, ты не можешь изменить "
                                  "режим общения, так как у тебя нет подписки 🌰",
                                  reply_markup=menu_keyboard.as_markup())
        await call.message.delete()


@system_settings_router.callback_query(F.data.startswith("ai_temperature"), any_state)
async def ai_temperature_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    ai_temperature = float(call.data.split("|")[1])
    await users_repository.update_ai_temperature_by_user_id(user_id, ai_temperature)
    await call.message.answer("Отлично, настройки твоего ассистента изменены!",
                              reply_markup=menu_keyboard.as_markup())
    await call.message.delete()


@system_settings_router.callback_query(F.data.startswith("edit_checkup"), any_state)
async def edit_checkup_time_call(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    checkup_id = int(call.data.split("|")[1])
    checkup = await checkup_repository.get_checkup_by_checkup_id(checkup_id=checkup_id)
    await state.set_state(InputMessage.edit_time_checkup)
    await state.update_data(checkup_id=checkup_id)
    await call.message.answer("Для того, чтобы продолжить, введи, пожалуйста время в которое, тебе отправлять чекАп"
                              f"\n\nСейчас данный чекап отправляется в {checkup.time_checkup.strftime('%H:%M')}",
                              reply_markup=menu_keyboard.as_markup())
    await call.message.delete()


@system_settings_router.message(F.text, InputMessage.edit_time_checkup)
async def enter_new_checkup_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    result = is_valid_time(message.text)
    state_data = await state.get_data()
    await state.clear()
    checkup_id = int(state_data.get("checkup_id"))
    if result:
        await checkup_repository.update_time_checkup_by_checkup_id(checkup_id=checkup_id,
                                                                   time_checkup=message.text)
        await message.answer(f"Отлично, теперь данный чекап будет отправляться в {message.text}",
                             reply_markup=menu_keyboard.as_markup())
        return
    await state.set_state(InputMessage.edit_time_checkup)
    await state.update_data(checkup_id=checkup_id)
    await message.answer("Введенное тобой время имеет неправильный формат. Пример - 13:45. Попробуй еще раз",
                         reply_markup=menu_keyboard.as_markup())
