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
from utils.gpt_generate_recommendations import generate_recommendations, generate_summary, generate_exercises, \
    generate_feedback_exercises


exercises_router = Router()

@exercises_router.callback_query(F.data == "exercises_by_problem")
async def exercises_by_problem_call(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    await call.message.answer_photo(caption=mechanic_dict.get("exercises_by_problem"),
                                    photo=exercises_photo)
    await asyncio.sleep(2)
    ended_fast_helps = await fast_help_repository.get_ended_fast_help_by_user_id(user_id=user_id)
    if ended_fast_helps is not None and len(ended_fast_helps) >= 1:
        result = await generate_feedback_for_user(call, state, bot)
        return
    await call.message.answer("🐾 Чтобы я дал тебе рекомендации получше — разбери со мной свою проблему")
    await asyncio.sleep(1)
    await call.message.answer("🐿 Где мы с тобой продолжим общение?🐾",
                              reply_markup=fast_help_keyboard.as_markup())
    await call.message.delete()


async def generate_feedback_for_user(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    delete_message = await call.message.answer(
        "Генерирую индивидуальное задание для тебя, это займет не более 5 секунд")
    await call.message.delete()
    user_summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
    last_summary = await summary_user_repository.get_summary_by_user_id_and_number_summary(user_id=user_id,
                                                                                           number_summary=len(
                                                                                               user_summaries))
    user_problems = await mental_problems_repository.get_problems_by_summary_id(summary_id=last_summary.id)
    if user_problems is not None:
        mental_problems_data = {
            "self_esteem": user_problems.self_esteem,
            "emotions": user_problems.emotions,
            "relationships": user_problems.relationships,
            "love": user_problems.love,
            "career": user_problems.career,
            "finances": user_problems.finances,
            "health": user_problems.health,
            "self_actualization": user_problems.self_actualization,
            "burnout": user_problems.burnout,
            "spirituality": user_problems.spirituality,
        }
    else:
        mental_problems_data = {problem: True for problem in [
            'self_esteem', 'emotions', 'relationships', 'love', 'career',
            'finances', 'health', 'self_actualization', 'burnout', 'spirituality'
        ]}
    exercises = generate_exercises(mental_problems_data)
    user_exercise = await exercises_user_repository.add_exercise(user_id=user_id, exercise=exercises)
    await state.set_state(InputMessage.enter_answer_exercise)
    await state.update_data(exercises=user_exercise)
    await call.message.answer(user_exercise.exercise + "\n\n" + "Ответ на данное упражнение ты можешь написать в чат."
                                                   " Если ты перейдешь обратно в меню, то"
                                                   " на данное упражнение ответить будет нельзя",
                              reply_markup=menu_keyboard.as_markup())
    await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)


@exercises_router.message(F.text, InputMessage.enter_answer_exercise)
async def exercises_message_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    state_data = await state.get_data()
    exercises: ExercisesUser = state_data.get("exercises")
    await state.clear()
    if exercises is None:
        await message.answer("У тебя нет упражнения,  на которое можно ответить",
                             reply_markup=menu_keyboard.as_markup())
        return
    await exercises_user_repository.update_answer_by_exercise_id(exercises.id, user_answer=message.text)
    feedback = generate_feedback_exercises(exercise=exercises.exercise,
                                                 user_answer=message.text)
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Хочу еще упражнения", callback_data="more_exercises"))
    keyboard.row(menu_button)
    await message.answer(feedback, reply_markup=keyboard.as_markup())


@exercises_router.callback_query(F.data == "more_exercises", any_state)
async def more_exercises_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    # await call.message.answer(mechanic_dict.get("exercises_by_problem"))
    # await asyncio.sleep(2)
    await bot.send_chat_action(chat_id=call.from_user.id, action="typing")
    ended_go_deeper = await go_deeper_repository.get_ended_go_deeper_by_user_id(user_id=user_id)
    if ended_go_deeper is not None and len(ended_go_deeper) >= 1:
        result = await generate_feedback_for_user(call, state, bot)
        return
    await call.message.answer("🐾 Чтобы я дала тебе рекомендации получше — разбери со мной ещё одну ситуацию")
    await asyncio.sleep(1)
    await call.message.answer("🐿 Что на сей раз с тобой обсудим?🐾",
                              reply_markup=go_deeper_keyboard.as_markup())
    await call.message.delete()

