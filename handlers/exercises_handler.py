import asyncio
import datetime

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery, InputFile, BufferedInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.keyboards import menu_keyboard, fast_help_keyboard, mental_helper_keyboard, menu_button, go_deeper_keyboard
from db.models import ExercisesUser
from db.repository import fast_help_repository, fast_help_dialog_repository, \
    go_deeper_repository, go_deeper_dialogs_repository, operation_repository, summary_user_repository, \
    mental_problems_repository, exercises_user_repository
from settings import InputMessage, mechanic_text, mechanic_checkup, is_valid_email, fast_help_promt, go_deeper_promt, \
    mechanic_dict, exercises_photo
from utils.gpt_distributor import user_request_handler
from utils.gpt_generate_recommendations import generate_recommendations, generate_summary, generate_exercises, \
    generate_feedback_exercises


exercises_router = Router()

@exercises_router.callback_query(F.data == "exercises_by_problem")
async def exercises_by_problem_call(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    await call.message.answer_photo(caption=mechanic_dict.get("exercises_by_problem"),
                                    photo=exercises_photo)

    await call.message.delete()
    await generate_feedback_for_user(call, state, bot)


async def generate_feedback_for_user(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    delete_message = await call.message.answer(
        "📙Генерирую <b>индивидуальное</b> задание для тебя!")

    exercise = await user_request_handler.psy_handler.generate_exercise(user_id)
    await call.message.answer(exercise + "\n\n" + "Ответ на упражнение пиши в любое время",
                              reply_markup=menu_keyboard.as_markup())
    await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)

