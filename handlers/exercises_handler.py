import logging
from random import choice

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots import main_bot
from data.images import exercises_photo
from data.keyboards import menu_keyboard, get_sub_keyboard, discuss_problem_keyboard, \
    create_practice_exercise_recommendation_keyboard
from data.message_templates import messages_dict
from db.repository import user_counters_repository, mental_problems_repository
from utils.gpt_distributor import user_request_handler
from utils.limits import decrease_exercises_limit
from utils.messages_provider import send_long_markdown_message
from utils.subscription import get_user_subscription

exercises_router = Router()

logger = logging.getLogger(__name__)

@exercises_router.callback_query(F.data == "choose_exercise_problem")
async def choose_exercise_problem(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    user_counters = await user_counters_repository.get_user_counters(user_id)
    if not user_counters.used_exercises or user_counters.used_exercises < 3:
        await call.message.answer_photo(caption=messages_dict["exercises_mechanic_text"],
                                        photo=exercises_photo)
    try:
        await call.message.delete()
    except TelegramBadRequest as e:
        logger.error(str(e))

    problems = await mental_problems_repository.get_problems_by_user_id(user_id=user_id, worked_out_threshold=4)
    if not problems:
        problems = await mental_problems_repository.get_problems_by_user_id(user_id=user_id)
    problems = sorted(problems, key=lambda p: p.worked_out)[:3]

    if problems:
        keyboard_builder = InlineKeyboardBuilder()
        problem_titles = set()
        for problem in problems:
            if not problem.problem_title in problem_titles:
                keyboard_builder.row(InlineKeyboardButton(
                    text=problem.problem_title,
                    callback_data=f"exercise_by_problem_id|{problem.id}"
                ))
                problem_titles.add(problem.problem_title)
        keyboard_builder.row(InlineKeyboardButton(
            text="🎲 Универсальные упражнения", callback_data="choose_exercise_FUX"
        ))
        keyboard_builder.row(InlineKeyboardButton(
            text="Отмена", callback_data="cancel"
        ))
        await call.message.answer(
            "Выбери проблему, которую хочешь проработать, или доверь выбор мне",
            reply_markup=keyboard_builder.as_markup()
        )
    else:
        await call.message.answer("Сначала разбери со мной проблему в чате!",
                                  reply_markup=discuss_problem_keyboard.as_markup())



@exercises_router.callback_query(F.data.startswith("choose_exercise_FUX"))
async def choose_exercise_fux(call: CallbackQuery, state: FSMContext, bot: Bot):
    problems = await mental_problems_repository.get_problems_by_user_id(user_id=0, worked_out_threshold=4)
    if not problems:
        problems = await mental_problems_repository.get_problems_by_user_id(user_id=0)

    problem = choice(problems)
    await send_exercise(call, bot, problem.id)

@exercises_router.callback_query(F.data.startswith("exercise_by_problem_id"))
async def send_exercise_by_problem_id(call: CallbackQuery, state: FSMContext, bot: Bot):
    problem_id = int(call.data.split('|')[1])
    await send_exercise(call, bot, problem_id)

@exercises_router.callback_query(F.data.startswith("deep_recommendation_by_problem_id"))
async def go_deeper_problem(call: CallbackQuery, state: FSMContext, bot: Bot):
    problem_id = int(call.data.split('|')[1])
    await go_deeper(call, bot, problem_id)


async def send_exercise(call: CallbackQuery, bot: Bot, problem_id: int):
    user_id = call.from_user.id

    if await decrease_exercises_limit(user_id) or await get_user_subscription(user_id):
        delete_message = await call.message.answer(
            "⏱️ Одну секунду! Загружаю <b>упражнение</b>..."
        )

        exercise = await user_request_handler.AI_handler.generate_exercise(user_id, problem_id)

        await send_long_markdown_message(user_id, exercise)

        await call.message.answer(messages_dict["exercise_conversation_welcome_text"], reply_markup=menu_keyboard.as_markup())

        await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)
    else:
        await main_bot.send_message(
            user_id,
            messages_dict["exercises_subscription_text"],
            reply_markup=(await get_sub_keyboard(user_id)).as_markup()
        )

async def go_deeper(call: CallbackQuery, bot: Bot, problem_id: int):
    user_id = call.from_user.id

    if await decrease_exercises_limit(user_id) or await get_user_subscription(user_id):
        delete_message = await call.message.answer(
            messages_dict["typing_message_text"]
        )

        exercise = await user_request_handler.AI_handler.generate_exercise(user_id, problem_id, deep_recommendation=True)

        await send_long_markdown_message(user_id, exercise)

        await call.message.answer(messages_dict["exercise_conversation_welcome_text"],
                                  reply_markup=create_practice_exercise_recommendation_keyboard(problem_id, True))

        await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)
    else:
        await main_bot.send_message(
            user_id,
            messages_dict["exercises_subscription_text"],
            reply_markup=(await get_sub_keyboard(user_id)).as_markup()
        )

