import asyncio
import logging
import re
from asyncio import Lock
from random import choice
from typing import Dict

from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import BufferedInputFile

from bots import main_bot
from data.keyboards import get_rec_keyboard, buy_sub_keyboard, create_practice_exercise_recommendation_keyboard
from db.repository import users_repository, ai_requests_repository, mental_problems_repository, \
    exercises_user_repository
from utils.documents import convert_to_pdf
from utils.gpt_client import BASIC_MODEL, ADVANCED_MODEL, ModelChatThread, LLMProvider
from utils.photo_recommendation import generate_blurred_image_with_text
from utils.prompts import RECOMMENDATION_PROMPT, \
    MENTAL_PROBLEM_SUMMARY_PROMPT, EXERCISE_PROMPT_FORMAT, DIALOG_CHECK_PROMPT, \
    DEFAULT_ASSISTANT_SYSTEM_PROMPT, get_assistant_system_prompt
from utils.subscription import check_is_subscribed
from utils.text import split_long_message
from utils.user_properties import get_user_description
from utils.user_request_types import UserRequest

logger = logging.getLogger(__name__)


class UserRequestHandler:
    def __init__(self):
        self.AI_handler = PsyHandler()

    async def handle(self, request: UserRequest):
        await users_repository.user_sent_message(request.user_id)

        if request.file is not None and request.file.file_type == 'document':
            if not request.file.filename.endswith('pdf'):
                request.file.filename, request.file.file_bytes = await convert_to_pdf(request.file.filename,
                                                                                request.file.file_bytes)


        if await check_is_subscribed(request.user_id):
            await self.AI_handler.handle(request)
        else:
            await asyncio.sleep(2)
            if request.file is None:
                if await LLMProvider.is_text_smalltalk(request.text) \
                        or await self.AI_handler.check_is_dialog_psy_now(request):
                    await self.AI_handler.handle(request)
                else:
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы общаться с 🤖 <i>универсальным ассистентом</i> — оформи <b>подписку</b>",
                        reply_markup=buy_sub_keyboard.as_markup()
                    )
            else:
                if request.file.file_type == 'image':
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы я смог считывать твои 🌇 <i>фотографии</i> — оформи <b>подписку</b>",
                        reply_markup=buy_sub_keyboard.as_markup()
                    )
                elif request.file.file_type == 'voice':
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы я смог считывать твои 🎙️ <i>голосовые сообщения</i> — оформи <b>подписку</b>",
                        reply_markup=buy_sub_keyboard.as_markup()
                    )
                elif request.file.file_type == 'document':
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы я смог считывать твои 📁 <i>файлы</i> — оформи <b>подписку</b>",
                        reply_markup=buy_sub_keyboard.as_markup()
                    )


class AIHandler:
    assistant_id: str

    def __init__(self):
        self.active_threads: Dict[int, ModelChatThread | None] = {}
        self.thread_locks = {}
        self.basic_model_provider = LLMProvider(BASIC_MODEL)
        self.advanced_model_provider = LLMProvider(ADVANCED_MODEL)

    async def handle(self, request: UserRequest):
        typing_message = await main_bot.send_message(
            request.user_id,
            "💬<i>Печатаю…</i>"
        )
        try:
            await main_bot.send_chat_action(chat_id=request.user_id, action="typing")
        except TelegramRetryAfter:
            pass

        if not self.thread_locks.get(request.user_id):
            self.thread_locks[request.user_id] = Lock()

        async with self.thread_locks[request.user_id]:
            await self.create_message(request)

            result = await self.run_thread(request.user_id)

        message_text = re.sub(r'【.*】.', '', result)
        messages = split_long_message(message_text)
        for message in messages:
            await main_bot.send_message(
                request.user_id,
                message,
                parse_mode=""
            )

        await ai_requests_repository.add_request(
            user_id=request.user_id,
            user_question=request.text,
            answer_ai=result,
            has_photo=request.file and request.file.file_type == 'image',
            has_audio=request.file and request.file.file_type == 'voice',
            has_files=request.file and request.file.file_type == 'document'
            )

        await typing_message.delete()


    async def run_thread(self, user_id, save_answer: bool = True) -> str | None:
        if self.active_threads.get(user_id):
            input = self.active_threads[user_id].get_messages()
            result = await self.basic_model_provider.process_request(input)

            if save_answer:
                self.active_threads[user_id].add_message(
                    LLMProvider.create_message(
                        content=[
                            await LLMProvider.create_text_content_item(
                                result
                            )
                        ],
                        role="assistant"
                    )
                )
            return result
        return None

    async def create_message(self, request: UserRequest) -> int:
        if not self.active_threads.get(request.user_id):
            user_description = await get_user_description(request.user_id, True)
            system_prompt = await get_assistant_system_prompt(request.user_id)
        else:
            user_description = ""
            system_prompt = DEFAULT_ASSISTANT_SYSTEM_PROMPT
        if user_description and not self.active_threads.get(request.user_id):
            self.active_threads[request.user_id] = ModelChatThread()
            self.active_threads[request.user_id].add_message(
                LLMProvider.create_message(
                    content=[
                        await LLMProvider.create_text_content_item(
                            system_prompt
                        )
                    ],
                    role="system"
                )
            )
            self.active_threads[request.user_id].add_message(
                LLMProvider.create_message(
                    role="model",
                    content=[
                        await LLMProvider.create_text_content_item(
                            "Мои конспекты с информацией о пользователе:\n" + user_description
                        )
                    ]
                )
            )

        content = []

        if request.text:
            content.append(
                await LLMProvider.create_text_content_item(request.text)
            )

        if request.file:
            if request.file.file_type == "image":
                content.append(
                    await LLMProvider.create_image_content_item(
                        request.file
                    )
                )
            elif request.file.file_type == "voice":
                content.append(
                    await LLMProvider.create_voice_content_item(
                        request.file
                    )
                )
            elif request.file.file_type == "document":
                content.append(
                    await LLMProvider.create_document_content_item(
                        request.file
                    )
                )

        if content:
            pass
        else:
            content = "Расскажи о себе"

        return self.active_threads[request.user_id].add_message(
                LLMProvider.create_message(
                    content=content,
                    role="user"
                )
            )

    async def exit(self, user_id: int):
        if self.thread_locks.get(user_id):
            async with self.thread_locks[user_id]:
                self.active_threads[user_id] = None


    async def check_is_dialog_psy_now(self, request: UserRequest) -> bool:
        if not self.thread_locks.get(request.user_id):
            self.thread_locks[request.user_id] = Lock()

        async with self.thread_locks[request.user_id]:
            check_request = UserRequest(
                user_id=request.user_id,
                text=DIALOG_CHECK_PROMPT
            )

            message_id = await self.create_message(request)
            check_message_id = await self.create_message(check_request)

            result = False
            response = await self.run_thread(request.user_id, False)
            logger.info(f"Checker response: {response}")
            result = 'true' in response.lower()

            self.active_threads[request.user_id].delete_message(message_id)
            self.active_threads[request.user_id].delete_message(check_message_id)

        return result



class PsyHandler(AIHandler):
    messages_count = {}
    MESSAGES_LIMIT = 6

    async def handle(self, request: UserRequest):
        if not self.messages_count.get(request.user_id):
            self.messages_count[request.user_id] = 0
        self.messages_count[request.user_id] += 1

        if self.messages_count[request.user_id] <= self.MESSAGES_LIMIT or await check_is_subscribed(request.user_id):
            await super().handle(request)
        else:
            await self.provide_recommendations(request.user_id)

    async def provide_recommendations(self, user_id: int, from_notification: bool = False):
        typing_message = await main_bot.send_message(
            user_id,
            "💬<i>Печатаю…</i>"
        )

        try:
            await main_bot.send_chat_action(chat_id=user_id, action="typing")
        except TelegramRetryAfter:
            pass
        await users_repository.user_got_recommendation(user_id)

        user = await users_repository.get_user_by_user_id(user_id)
        is_subscribed = await check_is_subscribed(user_id)

        if self.thread_locks.get(user_id) and self.active_threads.get(user_id) and await self.check_is_dialog_psy_now(
            UserRequest(
                user_id=user_id,
                text=" "
            )
        ):
            async with self.thread_locks[user_id]:
                recommendation_request = UserRequest(
                    user_id=user_id,
                    text=RECOMMENDATION_PROMPT
                )
                await self.create_message(recommendation_request)

                recommendation = await self.run_thread(user_id, save_answer=False)


            if not user.used_free_recommendation or is_subscribed:
                await main_bot.send_message(
                    user_id,
                    f"<b>{recommendation}</b>\n\n{'Ты всегда можешь получить рекомендацию с /recommendation' if from_notification else ''}"
                ) # Дать рекомендации
                await main_bot.send_chat_action(
                    user_id,
                    action="record_voice"
                )
                voice_file = await LLMProvider.generate_speech(recommendation)
                await main_bot.send_chat_action(
                    user_id,
                    action="upload_voice"
                )
                logger.info("exiting thread...")
                problem_id = await self.exit(user_id)
                logger.info("sending voice")
                await main_bot.send_voice(
                    user_id,
                    voice_file,
                    reply_markup=create_practice_exercise_recommendation_keyboard(problem_id)
                )

                if not is_subscribed:
                    await users_repository.used_free_recommendation(user_id)

            else:
                photo_recommendation = generate_blurred_image_with_text(text=recommendation, enable_blur=True)
                await main_bot.send_photo(
                    user_id,
                    has_spoiler=True,
                    photo=BufferedInputFile(file=photo_recommendation, filename=f"recommendation.png"),
                    caption=
                    f"🌰<i>Рекомендация</i> готова, но чтобы получить её, нужна <b>подписка</b>"
                    f"\n\n{'Ты всегда можешь получить рекомендацию с /recommendation' if from_notification else ''}",
                    reply_markup=get_rec_keyboard(mode_type="fast_help").as_markup())

        else:
            await main_bot.send_message(
                user_id,
                "Для того, чтобы получить рекомендацию, обсуди проблему"
            )


        await typing_message.delete()
        await self.exit(user_id)

    async def generate_exercise(self, user_id: int, problem_id: int | None = None) -> str | None:
        if problem_id is None:
            problems = await mental_problems_repository.get_problems_by_user_id(user_id=user_id, worked_out_threshold=4)
            if not problems:
                problems = await mental_problems_repository.get_problems_by_user_id(user_id=user_id)
                if not problems:
                    return None
            problem = choice(problems)
        else:
            problem = await mental_problems_repository.get_problem_by_id(problem_id=problem_id)

        await users_repository.used_exercises(user_id)

        exercise_text = await self.advanced_model_provider.process_request(
                EXERCISE_PROMPT_FORMAT.format(
                problem_summary=problem.problem_summary
            )
        )


        await exercises_user_repository.add_exercise(
            user_id=user_id,
            text=exercise_text,
            problem_id=problem.id
        )
        await mental_problems_repository.worked_out(problem.id)

        return exercise_text


    async def summarize_dialog_problem(self, user_id: int) -> int | None:
        logger.info("Summarizing dialog...")
        user = await users_repository.get_user_by_user_id(user_id)
        if user:
            if self.thread_locks.get(user_id):
                async with self.thread_locks[user_id]:
                    if self.active_threads.get(user_id):
                        summary_request = UserRequest(
                            user_id=user_id,
                            text=MENTAL_PROBLEM_SUMMARY_PROMPT
                        )

                        await self.create_message(summary_request)

                        problem_summary = await self.run_thread(user_id)



                        return await mental_problems_repository.add_problem(
                            user_id=user_id,
                            problem_summary=problem_summary
                        )

        return None

    async def exit(self, user_id: int) -> int | None:
        if self.active_threads.get(user_id):
            if await self.check_is_dialog_psy_now(UserRequest(user_id=user_id, text=" ")):
                problem_id = await self.summarize_dialog_problem(user_id)
            else:
                problem_id = None

            await super().exit(user_id)

            self.messages_count[user_id] = 0

            return problem_id
        return None


user_request_handler = UserRequestHandler()