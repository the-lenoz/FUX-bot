import asyncio
import logging
from asyncio import Lock
from random import choice
from typing import Dict

import telegramify_markdown
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.types import BufferedInputFile
from telegramify_markdown import ContentTypes, InterpreterChain, TextInterpreter, FileInterpreter, MermaidInterpreter

from bots import main_bot
from data.keyboards import buy_sub_keyboard, create_practice_exercise_recommendation_keyboard
from db.repository import users_repository, ai_requests_repository, mental_problems_repository, \
    exercises_user_repository, recommendations_repository, limits_repository, pending_messages_repository, \
    user_counters_repository
from settings import messages_dict
from utils.documents import convert_to_pdf
from utils.gpt_client import BASIC_MODEL, ADVANCED_MODEL, ModelChatThread, LLMProvider
from utils.photo_recommendation import generate_blurred_image_with_text
from utils.prompts import RECOMMENDATION_PROMPT, \
    MENTAL_PROBLEM_ABSTRACT_PROMPT, EXERCISE_PROMPT_FORMAT, DIALOG_LATEST_MESSAGE_CHECKER_PROMPT, \
    DEFAULT_ASSISTANT_PROMPT_ADDON, get_assistant_system_prompt, DIALOG_CHECKER_PROMPT, MENTAL_PROBLEM_TITLE_PROMPT
from utils.subscription import check_is_subscribed
from utils.user_properties import get_user_description
from utils.user_request_types import UserRequest

logger = logging.getLogger(__name__)


class UserRequestHandler:
    def __init__(self):
        self.AI_handler = PsyHandler()

    async def handle(self, request: UserRequest):
        await user_counters_repository.user_sent_message(request.user_id)

        if request.file is not None and request.file.file_type == 'document':
            if not request.file.filename.endswith('pdf'):
                request.file.filename, request.file.file_bytes = await convert_to_pdf(request.file.filename,
                                                                                request.file.file_bytes)
        if not self.AI_handler.thread_locks.get(request.user_id):
            self.AI_handler.thread_locks[request.user_id] = Lock()
        async with self.AI_handler.thread_locks[request.user_id]:
            if await check_is_subscribed(request.user_id):
                await self.AI_handler.handle(request)
            else:
                await asyncio.sleep(2)
                limits = await limits_repository.get_user_limits(user_id=request.user_id)
                if request.file is None:
                    if await LLMProvider.is_text_smalltalk(request.text):
                        await self.AI_handler.handle(request)
                    elif await self.AI_handler.check_is_dialog_latest_message_psy(request):
                        if limits.psychological_requests_remaining:
                            await limits_repository.update_user_limits(user_id=request.user_id,
                                                                       psychological_requests_remaining=limits.psychological_requests_remaining - 1)
                            await self.AI_handler.handle(request)
                        else:
                            await main_bot.send_message(
                                request.user_id,
                                messages_dict["mental_assistant_subscription_text"],
                                reply_markup=buy_sub_keyboard.as_markup()
                            )
                    else:
                        if limits.universal_requests_remaining:
                            await limits_repository.update_user_limits(user_id=request.user_id,
                                                                       universal_requests_remaining=limits.universal_requests_remaining - 1)
                            await self.AI_handler.handle(request)
                        else:
                            await main_bot.send_message(
                                request.user_id,
                                messages_dict["universal_assistant_subscription_text"],
                                reply_markup=buy_sub_keyboard.as_markup()
                            )
                else:
                    if request.file.file_type == 'image':
                        if limits.attachments_remaining:
                            await limits_repository.update_user_limits(
                                user_id=request.user_id,
                                attachments_remaining=limits.attachments_remaining - 1
                            )
                            await self.AI_handler.handle(request)
                        else:
                            await main_bot.send_message(
                                request.user_id,
                                messages_dict["send_photos_subscription_text"],
                                reply_markup=buy_sub_keyboard.as_markup()
                            )
                    elif request.file.file_type == 'voice':
                        if limits.voices_remaining:
                            await limits_repository.update_user_limits(
                                user_id=request.user_id,
                                voices_remaining=limits.voices_remaining - 1
                            )
                            await self.AI_handler.handle(request)
                        else:
                            await main_bot.send_message(
                                request.user_id,
                                messages_dict["send_voice_subscription_text"],
                                reply_markup=buy_sub_keyboard.as_markup()
                            )
                    elif request.file.file_type == 'document':
                        if limits.attachments_remaining:
                            await limits_repository.update_user_limits(
                                user_id=request.user_id,
                                attachments_remaining=limits.attachments_remaining - 1
                            )
                            await self.AI_handler.handle(request)
                        else:
                            await main_bot.send_message(
                                request.user_id,
                                messages_dict["send_document_subscription_text"],
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
            messages_dict["typing_message_text"]
        )
        try:
            await main_bot.send_chat_action(chat_id=request.user_id, action="typing")
        except TelegramRetryAfter:
            pass
        await self.create_message(request)

        result = await self.run_thread(request.user_id)

        interpreter_chain = InterpreterChain([
            TextInterpreter(),  # Use pure text first
            FileInterpreter(),  # Handle code blocks
            MermaidInterpreter(session=None),  # Handle Mermaid charts
        ])

        boxs = await telegramify_markdown.telegramify(
            content=result,
            interpreters_use=interpreter_chain,
            latex_escape=True,
            normalize_whitespace=True,
            max_word_count=4090  # The maximum number of words in a single message.
        )

        for item in boxs:
            if item.content_type == ContentTypes.TEXT:
                await main_bot.send_message(
                    request.user_id,
                    item.content,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            elif item.content_type == ContentTypes.PHOTO:
                await main_bot.send_photo(
                    request.user_id,
                    BufferedInputFile(file=item.file_data, filename=item.file_name),
                    caption=item.caption,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            elif item.content_type == ContentTypes.FILE:
                await main_bot.send_document(
                    request.user_id,
                    BufferedInputFile(file=item.file_data, filename=item.file_name),
                    caption=item.caption,
                    parse_mode=ParseMode.MARKDOWN_V2
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
            if await check_is_subscribed(user_id):
                result = await self.advanced_model_provider.process_request(input)
            else:
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
            system_prompt = DEFAULT_ASSISTANT_PROMPT_ADDON
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
        self.active_threads[user_id] = None
        await user_counters_repository.user_ended_dialog(user_id)


    async def check_is_dialog_latest_message_psy(self, request: UserRequest) -> bool:
        check_request = UserRequest(
            user_id=request.user_id,
            text=DIALOG_LATEST_MESSAGE_CHECKER_PROMPT
        )

        message_id = await self.create_message(request)
        check_message_id = await self.create_message(check_request)

        response = await self.run_thread(request.user_id, False)
        logger.info(f"Checker response: {response}")
        result = 'true' in response.lower()

        self.active_threads[request.user_id].delete_message(message_id)
        self.active_threads[request.user_id].delete_message(check_message_id)

        return result

    async def check_is_dialog_psy(self, user_id: int) -> bool:
        check_request = UserRequest(
            user_id=user_id,
            text=DIALOG_CHECKER_PROMPT
        )
        check_message_id = await self.create_message(check_request)

        response = await self.run_thread(user_id, False)
        logger.info(f"Checker response: {response}")
        result = 'true' in response.lower()

        self.active_threads[user_id].delete_message(check_message_id)

        return result

class PsyHandler(AIHandler):
    messages_count = {}
    MESSAGES_NOTIFICATION_COUNT = {6, 20}
    VOICE_NOTIFICATION_COUNT = {15}
    DIALOG_NOTIFICATION_COUNT = {1, 3}

    async def handle(self, request: UserRequest):
        if not self.messages_count.get(request.user_id):
            self.messages_count[request.user_id] = 0
        self.messages_count[request.user_id] += 1

        user_counters = await user_counters_repository.get_user_counters(request.user_id)
        if (self.messages_count[request.user_id] + 1 in self.MESSAGES_NOTIFICATION_COUNT
                and user_counters.dialogs_count + 1 in self.DIALOG_NOTIFICATION_COUNT):
            await main_bot.send_message(request.user_id, messages_dict["recommendation_command_reminder_text"])
        if (self.messages_count[request.user_id] + 1 in self.VOICE_NOTIFICATION_COUNT
            and user_counters.dialogs_count + 1 in self.DIALOG_NOTIFICATION_COUNT
            and await check_is_subscribed(request.user_id)):
            await main_bot.send_message(request.user_id, messages_dict["voice_message_reminder_text"])
        await super().handle(request)

    @staticmethod
    async def send_recommendation(user_id: int, recommendation, problem_id: int, from_notification: bool = False):
        try:
            await main_bot.send_message(
                user_id,
                telegramify_markdown.markdownify(recommendation) + '\n\n' +
                (messages_dict["recommendation_command_reminder_text"] if from_notification else ''),
                parse_mode=ParseMode.MARKDOWN_V2
            )  # Дать рекомендации
        except TelegramBadRequest as e:
            logger.error(e)
            logger.error(recommendation)
        await main_bot.send_chat_action(
            user_id,
            action="record_voice"
        )
        user = await users_repository.get_user_by_user_id(user_id)
        voice_file = await LLMProvider.generate_speech(recommendation, user_ai_temperature=user.ai_temperature)
        await main_bot.send_chat_action(
            user_id,
            action="upload_voice"
        )
        logger.info("sending voice")
        await main_bot.send_voice(
            user_id,
            voice_file,
            reply_markup=create_practice_exercise_recommendation_keyboard(problem_id)
        )

    async def provide_recommendations(self, user_id: int, from_notification: bool = False):
        typing_message = await main_bot.send_message(
            user_id,
            messages_dict["typing_message_text"]
        )
        problem_id = None
        if self.thread_locks.get(user_id) and self.active_threads.get(user_id):
            async with self.thread_locks[user_id]:
                try:
                    await main_bot.send_chat_action(chat_id=user_id, action="typing")
                except TelegramRetryAfter:
                    pass
                await user_counters_repository.user_got_recommendation(user_id)

                user = await users_repository.get_user_by_user_id(user_id)
                is_subscribed = await check_is_subscribed(user_id)

                problem_id = await self.summarize_dialog_problem(user_id)

                if problem_id and self.active_threads.get(user_id):
                    recommendation_request = UserRequest(
                        user_id=user_id,
                        text=RECOMMENDATION_PROMPT
                    )
                    await self.create_message(recommendation_request)
                    recommendation = await self.run_thread(user_id, save_answer=False)
                    logger.info("exiting thread...")

                    recommendation_object = await recommendations_repository.add_recommendation(
                        user_id=user_id,
                        text=recommendation,
                        problem_id=problem_id
                    )

                    if not user.used_free_recommendation or is_subscribed:
                        await self.send_recommendation(
                            user_id=user_id,
                            recommendation=recommendation,
                            problem_id=problem_id,
                            from_notification=from_notification
                        )

                        if not is_subscribed:
                            await users_repository.used_free_recommendation(user_id)

                    else:
                        await pending_messages_repository.update_user_pending_messages(user_id=user_id, recommendation_id=recommendation_object.id)
                        photo_recommendation = generate_blurred_image_with_text(text=recommendation, enable_blur=True)
                        await main_bot.send_photo(
                            user_id,
                            has_spoiler=True,
                            photo=BufferedInputFile(file=photo_recommendation, filename=f"recommendation.png"),
                            caption=messages_dict["subscribe_for_recommendation_text"],
                            reply_markup=buy_sub_keyboard.as_markup())

                else:
                    await main_bot.send_message(
                        user_id,
                        messages_dict["discuss_problem_for_recommendation_text"]
                    )


                await typing_message.delete()
        else:
            await main_bot.send_message(
                user_id,
                messages_dict["discuss_problem_for_recommendation_text"]
            )
        if problem_id or from_notification:
            await self.exit(user_id, save=False)

    async def generate_exercise(self, user_id: int, problem_id: int) -> str | None:
        problem = await mental_problems_repository.get_problem_by_id(problem_id=problem_id)

        await user_counters_repository.used_exercises(user_id)

        exercise_text = await self.advanced_model_provider.process_request(
            [
                LLMProvider.create_message(
                    [
                        await LLMProvider.create_text_content_item(
                            EXERCISE_PROMPT_FORMAT.format(
                                problem_summary=problem.problem_abstract
                            )
                        )
                    ],
                    "user"
                )
            ]
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

        if self.active_threads.get(user_id):
            summary_request = UserRequest(
                user_id=user_id,
                text=MENTAL_PROBLEM_ABSTRACT_PROMPT
            )

            await self.create_message(summary_request)

            problem_summary = await self.run_thread(user_id)

            title_request = UserRequest(
                user_id=user_id,
                text=MENTAL_PROBLEM_TITLE_PROMPT
            )

            await self.create_message(title_request)

            problem_title = await self.run_thread(user_id)

            return await mental_problems_repository.add_problem(
                user_id=user_id,
                problem_abstract=problem_summary,
                problem_title=problem_title
            )

        return None

    async def exit(self, user_id: int, save: bool = True) -> int | None:
        if self.thread_locks.get(user_id):
            async with self.thread_locks[user_id]:
                if self.active_threads.get(user_id):
                    if save and self.messages_count.get(user_id) >= 3 and await self.check_is_dialog_psy(user_id):
                        problem_id = await self.summarize_dialog_problem(user_id)
                    else:
                        problem_id = None

                    await super().exit(user_id)

                    self.messages_count[user_id] = 0

                    return problem_id
        return None


user_request_handler = UserRequestHandler()