import base64
import json
import logging
import re
import tempfile
from asyncio import Lock
from pprint import pprint
from random import choice
from typing import Dict

import openai
from aiogram.types import BufferedInputFile, FSInputFile
from pydantic import BaseModel

from bots import main_bot
from data.keyboards import get_rec_keyboard, buy_sub_keyboard, create_practice_exercise_recommendation_keyboard
from db.repository import users_repository, ai_requests_repository, mental_problems_repository, \
    exercises_user_repository
from utils.documents import convert_to_pdf
from utils.gpt_client import openAI_client, BASIC_MODEL, TRANSCRIPT_MODEL, mental_assistant_id, standard_assistant_id, \
    TTS_MODEL, ADVANCED_MODEL, ModelChatThread, ModelChatMessage
from utils.photo_recommendation import generate_blurred_image_with_text
from utils.prompts import PSY_TEXT_CHECK_PROMPT_FORMAT, IMAGE_CHECK_PROMPT, DOCUMENT_CHECK_PROMPT, \
    RECOMMENDATION_PROMPT, \
    MENTAL_PROBLEM_SUMMARY_PROMPT, EXERCISE_PROMPT_FORMAT, SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT, DIALOG_CHECK_PROMPT, \
    MENTAL_ASSISTANT_SYSTEM_PROMPT, STANDARD_ASSISTANT_SYSTEM_PROMPT
from utils.subscription import check_is_subscribed
from utils.text import split_long_message
from utils.user_properties import get_user_description

logger = logging.getLogger(__name__)

class UserFile(BaseModel):
    file_bytes: bytes
    file_type: str
    filename: str


class UserRequest(BaseModel):
    user_id: int
    text: str | None = None
    file: UserFile | None = None


class UserRequestHandler:
    def __init__(self):
        self.general_handler = GeneralHandler()
        self.psy_handler = PsyHandler()

    async def handle(self, request: UserRequest):
        await users_repository.user_sent_message(request.user_id)

        if request.file is not None and request.file.file_type == 'document':
            if not request.file.filename.endswith('pdf'):
                request.file.filename, request.file.file_bytes = await convert_to_pdf(request.file.filename,
                                                                                request.file.file_bytes)


        if await check_is_subscribed(request.user_id):
            to_psy = False
            text = request.text if request.text else ""

            if self.psy_handler.active_threads.get(request.user_id):
                to_psy = True

            if to_psy or await self.general_handler.check_is_dialog_psy_now(request):
                #message_id = await self.psy_handler.create_message(request)
                #self.psy_handler.active_threads[request.user_id].delete_message(message_id)

                #for message in self.general_handler.active_threads[request.user_id].get_messages():
                #    if message.role != "system":
                #        self.psy_handler.active_threads[request.user_id].add_message(message)

                await self.psy_handler.handle(request)
            else:
                await self.general_handler.handle(request)  # РАБОТАЕМ - к gpt
        else:
            if request.file is None:
                if self.psy_handler.active_threads.get(request.user_id) \
                        or await self.general_handler.check_is_dialog_psy_now(request):
                    await self.psy_handler.handle(request) # РАБОТАЕМ - к психологу
                else:
                    if await UserRequestHandler.is_text_smalltalk(request.text):
                        await self.general_handler.handle(request)  # Разрешаем приветствия и смол-ток
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

    @staticmethod
    async def is_text_smalltalk(text: str):
        try:
            response = await openAI_client.responses.create(
                model=BASIC_MODEL,
                input=SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT.format(text=text),
                max_output_tokens=32
            )
            return response.output_text == 'true'
        except openai.BadRequestError:
            return False

    @staticmethod
    async def is_text_mental(text: str):
        try:
            response = await openAI_client.responses.create(
                model=BASIC_MODEL,
                input=PSY_TEXT_CHECK_PROMPT_FORMAT.format(text=text),
                max_output_tokens=32
            )
            return response.output_text == 'true'
        except openai.BadRequestError:
            return False

    @staticmethod
    async def is_image_mental(image: UserFile):
        try:
            response = await openAI_client.chat.completions.create(
                model=BASIC_MODEL,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": IMAGE_CHECK_PROMPT},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/{image.filename.split('.')[-1]};base64,{base64.b64encode(image.file_bytes).decode()}"
                        }}
                    ]}
                ],
                max_tokens=32
            )

            return response.choices[0].message.content == "true"

        except openai.BadRequestError:
            return False

    @staticmethod
    async def is_document_mental(document_file_id: str):
        try:
            response = await openAI_client.chat.completions.create(
                model=BASIC_MODEL,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": DOCUMENT_CHECK_PROMPT},
                        {
                            "type": "file",
                            "file": {
                                "file_id": document_file_id
                            }
                        }
                    ]}
                ],
                max_tokens=32
            )

            return response.choices[0].message.content == "true"

        except openai.BadRequestError:
            return False


    @staticmethod
    async def get_transcription(voice: UserFile) -> str:
        try:
            transcript = await openAI_client.audio.transcriptions.create(
                model=TRANSCRIPT_MODEL,
                file=(voice.filename, voice.file_bytes),
                language="ru"
            )
            return transcript.text

        except openai.BadRequestError:
            return ""


class AIHandler:
    assistant_id: str

    def __init__(self):
        self.active_threads: Dict[int, ModelChatThread | None] = {}
        self.thread_locks = {}

    async def handle(self, request: UserRequest):
        typing_message = await main_bot.send_message(
            request.user_id,
            "💬<i>Печатаю…</i>"
        )
        await main_bot.send_chat_action(chat_id=request.user_id, action="typing")

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
        pprint(self.active_threads)
        response = await openAI_client.responses.create(
            model=ADVANCED_MODEL if await check_is_subscribed(user_id) else BASIC_MODEL,
            input=self.active_threads[user_id].get_messages()
        )

        result = response.output_text
        if save_answer:
            self.active_threads[user_id].add_message(
                ModelChatMessage(
                    role="assistant",
                    content=result
                )
            )
        return result





    async def create_message(self, request: UserRequest) -> int:
        if not self.active_threads.get(request.user_id):
            user_description = await get_user_description(request.user_id, isinstance(self, PsyHandler))
        else:
            user_description = ""
        if user_description and not self.active_threads.get(request.user_id):
            self.active_threads[request.user_id] = ModelChatThread()
            self.active_threads[request.user_id].add_message(
                ModelChatMessage(
                    role="system",
                    content=MENTAL_ASSISTANT_SYSTEM_PROMPT
                    if isinstance(self, PsyHandler) else STANDARD_ASSISTANT_SYSTEM_PROMPT
                )
            )
            self.active_threads[request.user_id].add_message(
                ModelChatMessage(
                    role="system",
                    content="Description of the client:\n" + user_description

                )
            )

        content = [
                {
                    "type": "input_text",
                    "text": request.text
                }
        ] if request.text else []

        if request.file:
            if request.file.file_type == "image":
                image_file = await openAI_client.files.create(
                    file=(request.file.filename, request.file.file_bytes),
                    purpose="vision"
                )

                content.append(
                    {
                        "type": "input_image",
                        "file_id": image_file.id,
                    },
                )
            elif request.file.file_type == "voice":
                text = await UserRequestHandler.get_transcription(request.file)
                if content:
                    content[0]["text"] += text
                elif text:
                    content.append({
                        "type": "input_text",
                        "text": text
                    })
            elif request.file.file_type == "document":
                document_file = await openAI_client.files.create(
                    file=(request.file.filename, request.file.file_bytes),
                    purpose="user_data"
                )
                content.append({
                    "type": "input_file",
                    "file_id": document_file.id,
                })

                if len(content) == 1:
                    content.append({
                        "type": "input_text",
                        "text": "Опиши файл"
                    })

        if content:
            pass
        else:
            content = "Расскажи о себе"

        return self.active_threads[request.user_id].add_message(
                ModelChatMessage(
                    role="user",
                    content=content
                )
            )

    async def exit(self, user_id: int):
        if self.thread_locks.get(user_id):
            async with self.thread_locks[user_id]:
                self.active_threads[user_id] = None



class PsyHandler(AIHandler):
    assistant_id = mental_assistant_id
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

        await main_bot.send_chat_action(chat_id=user_id, action="typing")
        await users_repository.user_got_recommendation(user_id)

        user = await users_repository.get_user_by_user_id(user_id)
        is_subscribed = await check_is_subscribed(user_id)

        if self.thread_locks.get(user_id):
            async with self.thread_locks[user_id]:
                if self.active_threads.get(user_id):
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
                response = await openAI_client.audio.speech.create(
                    model=TTS_MODEL,
                    voice="alloy",  # Выберите один из голосов: alloy, echo, fable, onyx, nova, shimmer
                    input=recommendation,
                    response_format="opus"  # mp3, opus, aac, flac, wav, pcm
                )
                logger.info("writing voice to file...")
                with tempfile.NamedTemporaryFile(mode="w+", suffix=".ogg") as voice_file:
                    response.stream_to_file(voice_file.name)
                    await main_bot.send_chat_action(
                        user_id,
                        action="upload_voice"
                    )
                    logger.info("exiting thread...")
                    problem_id = await self.exit(user_id)
                    logger.info("sending voice")
                    await main_bot.send_voice(
                        user_id,
                        FSInputFile(voice_file.name),
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

    @staticmethod
    async def generate_exercise(user_id: int, problem_id: int | None = None) -> str | None:
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

        response = await openAI_client.responses.create(
            input=EXERCISE_PROMPT_FORMAT.format(problem_summary=problem.problem_summary),
            model=ADVANCED_MODEL if await check_is_subscribed(user_id) else BASIC_MODEL,
        )

        exercise_text = response.output_text

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
        problem_id = await self.summarize_dialog_problem(user_id)
        await super().exit(user_id)
        self.messages_count[user_id] = 0

        return problem_id


class GeneralHandler(AIHandler):
    assistant_id = standard_assistant_id

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




user_request_handler = UserRequestHandler()