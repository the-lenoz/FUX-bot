import base64
import tempfile
from asyncio import Lock
import re

import openai
from aiogram.types import BufferedInputFile, FSInputFile
from pydantic import BaseModel

from bots import main_bot
from data.keyboards import get_rec_keyboard, buy_sub_keyboard, practice_exercise_recommendation_keyboard
from db.repository import users_repository, ai_requests_repository
from utils.gpt_client import openAI_client, BASIC_MODEL, TRANSCRIPT_MODEL, mental_assistant_id, standard_assistant_id, TTS_MODEL, ADVANCED_MODEL
from utils.photo_recommendation import generate_blurred_image_with_text
from utils.prompts import PSY_TEXT_CHECK_PROMPT_FORMAT, IMAGE_CHECK_PROMPT, DOCUMENT_CHECK_PROMPT, \
    RECOMMENDATION_PROMPT, \
    MENTAL_DATA_PROVIDER_PROMPT, EXERCISE_PROMPT_FORMAT, SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT
from utils.subscription import check_is_subscribed
from utils.user_properties import get_user_description


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

        if await check_is_subscribed(request.user_id):
            to_psy = False
            text = request.text if request.text else ""

            if self.psy_handler.active_threads.get(request.user_id):
                to_psy = True

            if request.file is not None and not to_psy:
                if request.file.file_type == 'image':
                    if await UserRequestHandler.is_image_mental(request.file):
                        to_psy = True
                elif request.file.file_type == 'voice':
                    text += '\n'
                    text += await UserRequestHandler.get_transcription(request.file)
                    request = UserRequest(
                        text=text,
                        user_id=request.user_id,
                        file=None
                    )
                elif request.file.file_type == 'document':
                    document_file = await openAI_client.files.create(
                        file=(request.file.filename, request.file.file_bytes),
                        purpose="assistants"
                    )
                    if await UserRequestHandler.is_document_mental(document_file.id):
                        to_psy = True

                    await openAI_client.files.delete(document_file.id)

            if to_psy or await UserRequestHandler.is_text_mental(text):
                await self.psy_handler.handle(request)
            else:
                await self.general_handler.handle(request)  # РАБОТАЕМ - к gpt
        else:
            if request.file is None:
                if await UserRequestHandler.is_text_mental(request.text) \
                        or self.psy_handler.active_threads.get(request.user_id):
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
        self.active_threads = {}
        self.thread_locks = {}

    async def handle(self, request: UserRequest):
        if not self.thread_locks.get(request.user_id):
            self.thread_locks[request.user_id] = Lock()
        async with self.thread_locks[request.user_id]:
            if self.active_threads.get(request.user_id):
                thread_id = self.active_threads[request.user_id]
            else:
                thread = await openAI_client.beta.threads.create()
                thread_id = thread.id
                self.active_threads[request.user_id] = thread.id
                await openAI_client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"Description of the client:\n{await get_user_description(request.user_id, isinstance(self, PsyHandler))}",
                )

            typing_message = await main_bot.send_message(
                request.user_id,
                "💬<i>Печатаю…</i>"
            )
            await main_bot.send_chat_action(chat_id=request.user_id, action="typing")

            content = [
                    {
                        "type": "text",
                        "text": request.text
                    }
            ] if request.text else []
            attachments = None
            if request.file:
                if request.file.file_type == "image":
                    image_file = await openAI_client.files.create(
                        file=(request.file.filename, request.file.file_bytes),
                        purpose="vision"
                    )

                    content.append(
                        {
                            "type": "image_file",
                            "image_file": {
                                "file_id": image_file.id,
                            }
                        }
                    )
                elif request.file.file_type == "voice":
                    text = await UserRequestHandler.get_transcription(request.file)
                    if content:
                        content[0]["text"] += text
                    elif text:
                        content.append({
                            "type": "text",
                            "text": text
                        })
                elif request.file.file_type == "document":
                    document_file = await openAI_client.files.create(
                        file=(request.file.filename, request.file.file_bytes),
                        purpose="assistants"
                    )

                    if not content:
                        content = "Опиши файл"

                    attachments = [{
                        "file_id": document_file.id,
                        "tools": [{"type": "file_search"}]
                    }]

            if content:
                pass
            else:
                content = "Расскажи о себе"

            await openAI_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
                attachments=attachments
            )

            run = await openAI_client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            if run.status == 'completed':
                messages = await openAI_client.beta.threads.messages.list(
                    thread_id=thread_id,
                    run_id=run.id  # Получить сообщения только из этого Run
                )
                await typing_message.delete()
                await main_bot.send_message(
                    request.user_id,
                    re.sub(r'【.*】.', '', messages.data[0].content[0].text.value),
                    parse_mode=""
                )
                await ai_requests_repository.add_request(
                    user_id=request.user_id,
                    user_question=request.text,
                    answer_ai=messages.data[0].content[0].text.value,
                    has_photo=request.file and request.file.file_type == 'image',
                    has_audio=request.file and request.file.file_type == 'voice',
                    has_files=request.file and request.file.file_type == 'document'
                )


    async def exit(self, user_id: int):
        if self.thread_locks.get(user_id):
            async with self.thread_locks[user_id]:
                if self.active_threads.get(user_id):
                    await openAI_client.beta.threads.delete(self.active_threads[user_id])
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
                    await openAI_client.beta.threads.messages.create(
                        thread_id=self.active_threads[user_id],
                        role="user",
                        content=RECOMMENDATION_PROMPT,
                    )

                    run = await openAI_client.beta.threads.runs.create_and_poll(
                        thread_id=self.active_threads[user_id],
                        assistant_id=self.assistant_id
                    )

                    if run.status == 'completed':
                        messages = await openAI_client.beta.threads.messages.list(
                            thread_id=self.active_threads[user_id],
                            run_id=run.id  # Получить сообщения только из этого Run
                        )

                        recommendation = messages.data[0].content[0].text.value


                        if not user.used_free_recommendation or is_subscribed:
                            await main_bot.send_message(
                                user_id,
                                recommendation
                            ) # Дать рекомендации
                            await main_bot.send_chat_action(
                                user_id,
                                action="record_voice"
                            )
                            response = await openAI_client.audio.speech.create(
                                model=TTS_MODEL,
                                voice="alloy",  # Выберите один из голосов: alloy, echo, fable, onyx, nova, shimmer
                                input=f"<b>{recommendation}</b>\n\n{'Ты всегда можешь получить рекомендацию с /recommendation' if from_notification else ''}",
                                response_format="opus"  # mp3, opus, aac, flac, wav, pcm
                            )
                            with tempfile.NamedTemporaryFile(mode="w+", suffix=".ogg") as voice_file:
                                response.stream_to_file(voice_file.name)
                                await main_bot.send_chat_action(
                                    user_id,
                                    action="upload_voice"
                                )
                                await main_bot.send_voice(
                                    user_id,
                                    FSInputFile(voice_file.name),
                                    reply_markup=practice_exercise_recommendation_keyboard.as_markup()
                                )

                            if not is_subscribed:
                                await users_repository.used_free_recommendation(user_id)

                        else:
                            photo_recommendation = generate_blurred_image_with_text(text=recommendation, enable_blur=True)
                            await main_bot.send_photo(
                                user_id,
                                has_spoiler=True,
                                photo=BufferedInputFile(file=photo_recommendation, filename=f"recommendation.png"),
                                caption="🌰<i>Рекомендация</i> готова, но чтобы получить её, нужна <b>подписка</b>",
                                reply_markup=get_rec_keyboard(mode_type="fast_help").as_markup())
        else:
            await main_bot.send_message(
                user_id,
                "Для того, чтобы получить рекомендацию, обсуди проблему"
            )


        await typing_message.delete()
        await self.exit(user_id)

    @staticmethod
    async def generate_exercise(user_id: int):

        await users_repository.used_exercises(user_id)

        user_description = await get_user_description(user_id, True)

        response = await openAI_client.responses.create(
            input=EXERCISE_PROMPT_FORMAT.format(user_description=user_description),
            model=ADVANCED_MODEL if await check_is_subscribed(user_id) else BASIC_MODEL,
        )

        exercise = response.output_text

        response = await openAI_client.responses.create(
            input=MENTAL_DATA_PROVIDER_PROMPT + "\n\nПользователю было дано задание КПТ:\n" + exercise,
            model=ADVANCED_MODEL if await check_is_subscribed(user_id) else BASIC_MODEL,
        )

        await users_repository.update_mental_data_by_user_id(
            user_id,
            response.output_text
        )

        return exercise


    async def update_user_mental_data(self, user_id: int):
        user = await users_repository.get_user_by_user_id(user_id)
        if user:
            request_text = MENTAL_DATA_PROVIDER_PROMPT + "\n\nCurrent information about user:\n" + str(user.mental_data)

            if self.thread_locks.get(user_id):
                async with self.thread_locks[user_id]:
                    if self.active_threads.get(user_id):
                        message = await openAI_client.beta.threads.messages.create(
                            thread_id=self.active_threads[user_id],
                            role="user",
                            content=request_text,
                        )

                        run = await openAI_client.beta.threads.runs.create_and_poll(
                            thread_id=self.active_threads[user_id],
                            model=BASIC_MODEL,
                            assistant_id=self.assistant_id
                        )

                        if run.status == 'completed':
                            messages = await openAI_client.beta.threads.messages.list(
                                thread_id=self.active_threads[user_id],
                                run_id=run.id  # Получить сообщения только из этого Run
                            )

                            new_mental_data = messages.data[0].content[0].text.value
                            await users_repository.update_mental_data_by_user_id(
                                user_id,
                                new_mental_data
                            )
                        await openAI_client.beta.threads.messages.delete(message_id=message.id,
                                                                         thread_id=self.active_threads[user_id])

    async def exit(self, user_id: int):
        await self.update_user_mental_data(user_id)
        await super().exit(user_id)
        self.messages_count[user_id] = 0


class GeneralHandler(AIHandler):
    assistant_id = standard_assistant_id


user_request_handler = UserRequestHandler()