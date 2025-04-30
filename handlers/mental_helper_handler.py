import asyncio
import traceback

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from data.keyboards import fast_help_keyboard, mental_helper_keyboard, \
    go_deeper_keyboard, get_rec_keyboard, get_go_deeper_rec_keyboard, end_fast_help_keyboard, \
    exercises_keyboard
from db.repository import users_repository, ai_requests_repository, subscriptions_repository, fast_help_repository, \
    fast_help_dialog_repository, \
    go_deeper_repository, go_deeper_dialogs_repository, summary_user_repository, \
    mental_problems_repository
from settings import InputMessage, fast_help_promt, go_deeper_promt, \
    mental_helper_photo
from utils.get_problems_by_summary import get_problems_by_summary_user
from utils.gpt_generate_recommendations import generate_recommendations, generate_summary
from utils.photo_recommendation import generate_blurred_image_with_text
from utils.rating_chat_gpt import GPT

mental_router = Router()


@mental_router.callback_query(F.data == "mental_helper", any_state)
async def mental_start_message(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user_fast_help = await fast_help_repository.get_fast_helps_by_user_id(user_id=user_id)
    user_go_deeper = await go_deeper_repository.get_go_deepers_by_user_id(user_id=user_id)
    if (user_fast_help is not None and len(user_fast_help) != 0) and\
            (user_go_deeper is not None and len(user_go_deeper) != 0 and not(len(user_go_deeper) == 1 and user_go_deeper[0].end_go_deeper == False)):
        keyboard = mental_helper_keyboard
    elif (user_fast_help is None or len(user_fast_help) == 0) or (len(user_fast_help) == 1 and user_fast_help[0].end_fast_help == False):
        keyboard = fast_help_keyboard
    elif user_go_deeper is None or len(user_go_deeper) == 0 or (len(user_go_deeper) == 1 and user_go_deeper[0].end_go_deeper == False):
        keyboard = go_deeper_keyboard
    try:
        await call.message.answer_photo(
            photo=mental_helper_photo,
            reply_markup=keyboard.as_markup())
        await call.message.delete()
    except:
        print(traceback.format_exc())


@mental_router.callback_query(F.data == "fast_help_only", any_state)
@mental_router.callback_query(F.data == "fast_help", any_state)
async def mental_start_message(call: CallbackQuery, state: FSMContext, bot: Bot):
    if call.data == "fast_help_only":
        await call.message.answer("🐿️Давай в тестовом режиме разберём одну из твоих ситуаций. Я задам ровно <b>6 вопросов</b>"
                                  " и выдам подходящие под тебя рекомендации.")
        await call.message.answer("<b>Что ты хочешь со мной обсудить? 😅</b>")
    else:
        await call.message.answer("🧡<b>Здесь ты можешь быстро получить поддержку!</b> \n\nЗа счёт того, что я задаю только 6"
                                  " наводящих вопрос и сразу выдаю рекомендации, которые рассчитаны на то, чтобы тебе"
                                  " “здесь и сейчас” стало легче”")
    await call.message.edit_reply_markup(reply_markup=None)
    user_id = call.from_user.id
    user_fast_help = await fast_help_repository.get_active_fast_help_by_user_id(user_id=user_id)
    if user_fast_help is None:
        fast_helps_user = await fast_help_repository.get_fast_helps_by_user_id(user_id=user_id)
        if fast_helps_user is None:
            number_fast_help = 0
        else:
            number_fast_help = len(fast_helps_user)
        await fast_help_repository.add_fast_help(user_id=user_id, number_fast_help=number_fast_help + 1)
        user_fast_help = await fast_help_repository.get_active_fast_help_by_user_id(user_id=user_id)
    active_question = await fast_help_dialog_repository.get_active_fast_help_dialogs_by_fast_help_id(fast_help_id=user_fast_help.id)
    if active_question is not None:
        await state.set_state(InputMessage.enter_answer_fast_help)
        print(active_question.question)
        await call.message.answer(active_question.question)
        return
    await bot.send_chat_action(chat_id=call.from_user.id, action="typing")
    # delete_message = await call.message.answer("Формулирую вопрос, это займет не более 5 секунд")
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    ai_question = await GPT(thread_id=user.mental_ai_threat_id).send_message(user_id=user_id,
                                                                             text=fast_help_promt,
                                                                             temperature=user.ai_temperature,
                                                                             name=user.name,
                                                                             age=user.age,
                                                                             gender=user.gender)
    await ai_requests_repository.add_request(user_id=call.from_user.id,
                                             has_photo=False,
                                             answer_ai=ai_question,
                                             user_question=fast_help_promt)
    await fast_help_dialog_repository.add_fast_help_dialog(fast_help_id=user_fast_help.id,
                                                           question=ai_question)
    await state.set_state(InputMessage.enter_answer_fast_help)
    await call.message.answer(ai_question)
    # await bot.delete_message(chat_id=user_id, message_id=delete_message.message_id)



@mental_router.message(F.text, InputMessage.enter_answer_fast_help)
async def answer_fast_help_question (message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    await state.clear()
    user_fast_help = await fast_help_repository.get_active_fast_help_by_user_id(user_id=user_id)
    user_fast_help_dialog = await fast_help_dialog_repository.get_active_fast_help_dialogs_by_fast_help_id(fast_help_id=user_fast_help.id)
    if user_fast_help_dialog is None:
        return
    await fast_help_dialog_repository.update_answer_by_fast_help_dialog_id(fast_help_dialog_id=user_fast_help_dialog.id, answer=message.text)
    messages = await fast_help_dialog_repository.get_fast_help_dialogs_by_fast_help_id(fast_help_id=user_fast_help.id)
    if len(messages) >= 6:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        # delete_message = await message.answer("Генерирую рекомендацию на основе диалога, это займет не более 15 секунд")
        user = await users_repository.get_user_by_user_id(user_id=user_id)
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        user_all_fast_helps = await fast_help_repository.get_fast_helps_by_user_id(user_id=user_id)
        recommendation = await generate_recommendations(user_messages=messages)
        await fast_help_repository.update_recommendation_by_fast_help_id(fast_help_id=user_fast_help.id,
                                                                         recommendation=recommendation)
        user_summary = generate_summary(user_messages=messages)
        user_summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
        if user_summary is None or len(user_summaries) == 0:
            number_summaries = 0
        else:
            number_summaries = len(user_summaries)
        await summary_user_repository.add_summary_user(user_id=user_id, summary=user_summary,
                                                       number_summary=number_summaries + 1)
        if (user_sub is None and len(user_all_fast_helps) == 1) or user_sub:
            # photo_recommendation = generate_blurred_image_with_text(text=recommendation)
            # await message.answer(photo=BufferedInputFile(file=photo_recommendation,
            #                                                    filename=f"recommendation_{user_id}_"
            #                                                             f"{user_fast_help_dialog.fast_help_id}.png"))
            audio_file = await GPT(thread_id=user.mental_ai_threat_id).generate_audio_by_text(text=recommendation)
            audio_file.seek(0)  # сброс указателя в начало файла
            audio_bytes = audio_file.read()
            await message.answer(recommendation, reply_markup=end_fast_help_keyboard.as_markup())
                # Отправка голосового сообщения
            await message.answer_voice(
                voice=BufferedInputFile(file=audio_bytes, filename="voice.mp3")
            )
        else:
            photo_recommendation = generate_blurred_image_with_text(text=recommendation, enable_blur=True)
            await message.answer_photo(
                photo=BufferedInputFile(file=photo_recommendation,filename=f"recommendation_{user_id}_"
                                                                           f"{user_fast_help_dialog.fast_help_id}.png"),
                caption="🌰Для того, чтобы получить рекомендацию, нужно расколоть орех",
                reply_markup=get_rec_keyboard(mode_id=user_fast_help.id, mode_type="fast_help").as_markup())
        await state.clear()
        await fast_help_repository.update_ending_by_fast_help_id(fast_help_id=user_fast_help.id)
        # await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)
        last_summary = await summary_user_repository.get_summary_by_user_id_and_number_summary(user_id=user_id,
                                                                                               number_summary=number_summaries + 1)
        user_problems = get_problems_by_summary_user(summary=user_summary)
        user_problems["summary_id"] = last_summary.id
        await mental_problems_repository.add_mental_problems(**user_problems)
        return
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    # delete_message = await message.answer("Формулирую вопрос, это займет не более 5 секунд")
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    ai_question = await GPT(thread_id=user.mental_ai_threat_id).send_message(user_id=user_id,
                                                                             text=message.text + "\n\n" + fast_help_promt,
                                                                             temperature=user.ai_temperature,
                                                                             name=user.name,
                                                                             age=user.age,
                                                                             gender=user.gender)
    await ai_requests_repository.add_request(user_id=message.from_user.id,
                                             has_photo=False,
                                             answer_ai=ai_question,
                                             user_question=message.text)
    await asyncio.sleep(1)
    await fast_help_dialog_repository.add_fast_help_dialog(fast_help_id=user_fast_help.id,
                                                           question=ai_question)
    await message.answer(ai_question)
    await state.set_state(InputMessage.enter_answer_fast_help)
    # await bot.delete_message(chat_id=user_id, message_id=delete_message.message_id)


@mental_router.callback_query(F.data.startswith("get_recommendation"), any_state)
async def get_rec_after_sub(call: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    user_id = call.from_user.id
    call_data = call.data.split("|")
    mode_id = int(call_data[2])
    mode_type = call_data[1]
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
    if user_sub:
        user_fast_help = await fast_help_repository.get_fast_help_by_fast_help_id(fast_help_id=mode_id)
        recommendation = user_fast_help.recommendation
        await call.message.answer(recommendation)
        audio_file = await GPT(thread_id=user.mental_ai_threat_id).generate_audio_by_text(text=recommendation)
        audio_file.seek(0)  # сброс указателя в начало файла
        audio_bytes = audio_file.read()
        # Отправка голосового сообщения
        await call.message.answer_voice(
            voice=BufferedInputFile(file=audio_bytes, filename="voice.mp3")
        )
        await fast_help_repository.update_ending_by_fast_help_id(fast_help_id=user_fast_help.id)
        await call.message.delete()
        return
    await call.message.answer("Не видим, что ты приобрел подписку, для получения рекомендации(",
                              reply_markup=get_rec_keyboard(mode_id=mode_id, mode_type=mode_type).as_markup())
    await call.message.delete()


# @mental_router.callback_query(F.data.startswith("subscribe"), any_state)
# async def get_sub(call: CallbackQuery, state: FSMContext, bot: Bot):



@mental_router.callback_query(F.data.startswith("continue_go_deeper"), any_state)
@mental_router.callback_query(F.data == "go_deeper", any_state)
async def mental_start_message(call: CallbackQuery, state: FSMContext, bot: Bot):
    if call.data == "go_deeper":
        await call.message.answer("🧡<b>Здесь ты общаешься без ограничений!</b> \n\nЯ тебе задаю достаточное количество наводящих"
                                  " вопросов, чтобы уйти в глубь. И даю развёрнутые рекомендации направленные на"
                                  " долгосрочный эффект.\n\nА в платной версии ещё и используешь"
                                  " меня как универсального <b>AI-Ассистента</b>"
                                  )
    await call.message.edit_reply_markup(reply_markup=None)
    user_id = call.from_user.id
    await bot.send_chat_action(chat_id=call.from_user.id, action="typing")
    user_go_deeper = await go_deeper_repository.get_active_go_deeper_by_user_id(user_id=user_id)
    if user_go_deeper is None:
        go_deepers_user = await go_deeper_repository.get_go_deepers_by_user_id(user_id=user_id)
        if go_deepers_user is None:
            number_go_deeper = 0
        else:
            number_go_deeper = len(go_deepers_user)
        await go_deeper_repository.add_go_deeper(user_id=user_id, number_go_deeper=number_go_deeper + 1)
        user_go_deeper = await go_deeper_repository.get_active_go_deeper_by_user_id(user_id=user_id)
    active_question = await go_deeper_dialogs_repository.get_active_go_deeper_dialogs_by_fast_help_id(go_deeper_id=user_go_deeper.id)
    if active_question is not None:
        await state.set_state(InputMessage.enter_answer_go_deeper)
        await call.message.answer(active_question.question)
        return
    # delete_message = await call.message.answer("Формулирую вопрос, это займет не более 5 секунд")
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    ai_question = await GPT(thread_id=user.mental_ai_threat_id).send_message(user_id=user_id,
                                                                             text=go_deeper_promt,
                                                                             temperature=user.ai_temperature,
                                                                             name=user.name,
                                                                             age=user.age,
                                                                             gender=user.gender)
    await ai_requests_repository.add_request(user_id=call.from_user.id,
                                             has_photo=False,
                                             answer_ai=ai_question,
                                             user_question=go_deeper_promt)
    await go_deeper_dialogs_repository.add_go_deeper_dialog(go_deeper_id=user_go_deeper.id,
                                                           question=ai_question)
    await state.set_state(InputMessage.enter_answer_go_deeper)
    await call.message.answer(ai_question)
    # await bot.delete_message(chat_id=user_id, message_id=delete_message.message_id)


@mental_router.message(F.text, InputMessage.enter_answer_go_deeper)
async def answer_fast_help_question (message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await state.clear()
    user_go_deeper = await go_deeper_repository.get_active_go_deeper_by_user_id(user_id=user_id)
    user_go_deeper_dialog = await go_deeper_dialogs_repository.get_active_go_deeper_dialogs_by_fast_help_id(go_deeper_id=user_go_deeper.id)
    if user_go_deeper_dialog is None:
        return
    await go_deeper_dialogs_repository.update_answer_by_go_deeper_dialog_id(go_deeper_dialog_id=user_go_deeper_dialog.id, answer=message.text)
    messages = await go_deeper_dialogs_repository.get_go_deeper_dialogs_by_fast_help_id(go_deeper_id=user_go_deeper.id)
    if len(messages) >= 5:
        user = await users_repository.get_user_by_user_id(user_id=user_id)
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        user_go_deepers = await go_deeper_repository.get_go_deepers_by_user_id(user_id=user_id)

        if (user_sub is None and len(user_go_deepers) == 1) or user_sub:
            if not(len(user_go_deepers) == 1):
                ai_question = await GPT(thread_id=user.mental_ai_threat_id).send_message(user_id=user_id,
                                                                                         text=message.text,
                                                                                         temperature=user.ai_temperature,
                                                                                         name=user.name,
                                                                                         age=user.age,
                                                                                         gender=user.gender)
                await ai_requests_repository.add_request(user_id=message.from_user.id,
                                                         has_photo=False,
                                                         answer_ai=ai_question,
                                                         user_question=message.text)
                await go_deeper_dialogs_repository.add_go_deeper_dialog(go_deeper_id=user_go_deeper.id,
                                                                        question=ai_question)
                await state.set_state(InputMessage.enter_answer_go_deeper)
                await message.answer(text=ai_question,
                                     reply_markup=get_go_deeper_rec_keyboard(user_go_deeper.id).as_markup())
                return
            # photo_recommendation = generate_blurred_image_with_text(text=recommendation)
            # await message.answer_photo(photo=BufferedInputFile(file=photo_recommendation,
            #                                                    filename=f"recommendation_{user_id}_"
            #                                                             f"{user_go_deeper_dialog.go_deeper_id}.png"))
            recommendation = await generate_recommendations(user_messages=messages)
            await go_deeper_repository.update_recommendation_by_go_deeper_id(go_deeper_id=user_go_deeper.id,
                                                                             recommendation=recommendation)
            audio_file = await GPT(thread_id=user.mental_ai_threat_id).generate_audio_by_text(text=recommendation)
            audio_file.seek(0)  # сброс указателя в начало файла
            audio_bytes = audio_file.read()
            await message.answer(recommendation)
                # Отправка голосового сообщения
            await message.answer_voice(
                voice=BufferedInputFile(file=audio_bytes, filename="voice.mp3")
            )
            user_summary = generate_summary(user_messages=messages)
            user_summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
            if user_summary is None or len(user_summaries) == 0:
                number_summaries = 0
            else:
                number_summaries = len(user_summaries)
            await summary_user_repository.add_summary_user(user_id=user_id, summary=user_summary,
                                                           number_summary=number_summaries + 1)
            await message.answer("📙А ещё я могу дать тебе упражнение к этой проблеме",
                                 reply_markup=exercises_keyboard.as_markup())
        else:
            recommendation = await generate_recommendations(user_messages=messages[-10:])
            await go_deeper_repository.update_recommendation_by_go_deeper_id(go_deeper_id=user_go_deeper.id,
                                                                             recommendation=recommendation)
            user_summary = generate_summary(user_messages=messages)
            user_summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
            if user_summary is None or len(user_summaries) == 0:
                number_summaries = 0
            else:
                number_summaries = len(user_summaries)
            await summary_user_repository.add_summary_user(user_id=user_id, summary=user_summary,
                                                           number_summary=number_summaries + 1)
            photo_recommendation = generate_blurred_image_with_text(text=recommendation, enable_blur=True)
            await message.answer_photo(
                photo=BufferedInputFile(file=photo_recommendation, filename=f"recommendation_{user_id}_"
                                                                            f"{user_go_deeper_dialog.go_deeper_id}.png"),
                caption="🌰Для того, чтобы получить рекомендацию, нужно расколоть орех",
                reply_markup=get_rec_keyboard(mode_id=user_go_deeper.id, mode_type="go_deeper").as_markup())
        await go_deeper_repository.update_ending_by_go_deeper_id(go_deeper_id=user_go_deeper.id)
        last_summary = await summary_user_repository.get_summary_by_user_id_and_number_summary(user_id=user_id,
                                                                                               number_summary=number_summaries + 1)
        if last_summary is not None:
            user_problems = get_problems_by_summary_user(summary=user_summary)
            user_problems["summary_id"] = last_summary.id
            await mental_problems_repository.add_mental_problems(**user_problems)
        else:
            summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
            if summaries is not None and len(summaries) > 0:
                last_summary = summaries[-1]
                user_problems = get_problems_by_summary_user(summary=user_summary)
                user_problems["summary_id"] = last_summary.id
                await mental_problems_repository.add_mental_problems(**user_problems)
        return
    # delete_message = await message.answer("Формулирую вопрос, это займет не более 5 секунд")
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    ai_question = await GPT(thread_id=user.mental_ai_threat_id).send_message(user_id=user_id,
                                                                             text=message.text,
                                                                             temperature=user.ai_temperature,
                                                                             name=user.name,
                                                                             age=user.age,
                                                                             gender=user.gender)
    await ai_requests_repository.add_request(user_id=message.from_user.id,
                                             has_photo=False,
                                             answer_ai=ai_question,
                                             user_question=message.text)
    await go_deeper_dialogs_repository.add_go_deeper_dialog(go_deeper_id=user_go_deeper.id,
                                                           question=ai_question)
    await message.answer(ai_question)
    await state.set_state(InputMessage.enter_answer_go_deeper)
    # await bot.delete_message(chat_id=user_id, message_id=delete_message.message_id)


@mental_router.callback_query(F.data.startswith("get_go_deeper_rec"), any_state)
async def get_go_deeper_rec_message(call: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_chat_action(chat_id=call.from_user.id, action="typing")
    user_id = call.from_user.id
    call_data = call.data.split("|")
    go_deeper_id = int(call_data[1])
    await call.message.delete()
    user_go_deeper = await go_deeper_repository.get_go_deeper_by_go_deeper_id(go_deeper_id=go_deeper_id)
    messages = await go_deeper_dialogs_repository.get_go_deeper_dialogs_by_fast_help_id(go_deeper_id=user_go_deeper.id)
    messages = messages[:-1]
    recommendation = await generate_recommendations(user_messages=messages)
    await go_deeper_repository.update_recommendation_by_go_deeper_id(go_deeper_id=user_go_deeper.id,
                                                                     recommendation=recommendation)
    # photo_recommendation = generate_blurred_image_with_text(text=recommendation)
    # await call.message.answer_photo(photo=BufferedInputFile(file=photo_recommendation,
    #                                                    filename=f"recommendation_{user_id}.png"))
    # await call.message.answer(recommendation, reply_markup=menu_keyboard.as_markup())
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    audio_file = await GPT(thread_id=user.mental_ai_threat_id).generate_audio_by_text(text=recommendation)
    audio_file.seek(0)  # сброс указателя в начало файла
    audio_bytes = audio_file.read()
    await call.message.answer(recommendation)
    # Отправка голосового сообщения
    await call.message.answer_voice(
        voice=BufferedInputFile(file=audio_bytes, filename="voice.mp3")
    )
    user_summary = generate_summary(user_messages=messages)
    user_summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
    if user_summary is None or len(user_summaries) == 0:
        number_summaries = 0
    else:
        number_summaries = len(user_summaries)
    await summary_user_repository.add_summary_user(user_id=user_id, summary=user_summary,
                                                   number_summary=number_summaries + 1)
    await go_deeper_repository.update_ending_by_go_deeper_id(go_deeper_id=user_go_deeper.id)
    last_summary = await summary_user_repository.get_summary_by_user_id_and_number_summary(user_id=user_id,
                                                                                           number_summary=number_summaries + 1)
    if last_summary is not None:
        user_problems = get_problems_by_summary_user(summary=user_summary)
        user_problems["summary_id"] = last_summary.id
        await mental_problems_repository.add_mental_problems(**user_problems)
    else:
        summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user_id)
        if summaries is not None and len(summaries) > 0:
            last_summary = summaries[-1]
            user_problems = get_problems_by_summary_user(summary=user_summary)
            user_problems["summary_id"] = last_summary.id
            await mental_problems_repository.add_mental_problems(**user_problems)



