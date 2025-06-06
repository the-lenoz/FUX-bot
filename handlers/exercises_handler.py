import logging

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from data.keyboards import menu_keyboard
from db.repository import users_repository
from settings import mechanic_dict, exercises_photo
from utils.gpt_distributor import PsyHandler

exercises_router = Router()

logger = logging.getLogger(__name__)

@exercises_router.callback_query(F.data == "exercises_by_problem")
async def exercises_by_problem_call(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    user = await users_repository.get_user_by_user_id(user_id)
    if not user.used_exercises or user.used_exercises < 3:
        await call.message.answer_photo(caption=mechanic_dict.get("exercises_by_problem"),
                                        photo=exercises_photo)

    try:
        await call.message.delete()
    except TelegramBadRequest as e:
        logger.error(str(e))
    await generate_feedback_for_user(call, bot)


@exercises_router.callback_query(F.data.startswith("recommendation_exercise"))
async def exercises_by_recommendation(call: CallbackQuery, state: FSMContext, bot: Bot):
    problem_id = int(call.data.split('|')[1])
    await generate_feedback_for_user(call, bot, problem_id)


async def generate_feedback_for_user(call: CallbackQuery, bot: Bot, problem_id: int | None = None):
    user_id = call.from_user.id
    delete_message = await call.message.answer(
        "📙Генерирую <b>индивидуальное</b> задание для тебя!")

    exercise = await PsyHandler.generate_exercise(user_id, problem_id)
    if exercise:
        await call.message.answer(exercise + "\n\n" + "Ответ на упражнение пиши в любое время",
                                  reply_markup=menu_keyboard.as_markup())
    else:
        await call.message.answer("Сначала разбери со мной проблему в чате!", reply_markup=menu_keyboard.as_markup())
    await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)

