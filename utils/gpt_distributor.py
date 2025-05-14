import base64
import tempfile
from io import BytesIO

import openai
from aiogram.types import BufferedInputFile, FSInputFile
from pydantic import BaseModel

from bots import main_bot
from data.keyboards import get_rec_keyboard
from db.repository import users_repository
from utils.gpt_client import openAI_client, BASIC_MODEL, TRANSCRIPT_MODEL, mental_assistant_id, standard_assistant_id, \
    wait_for_run_completion, TTS_MODEL
from utils.photo_recommendation import generate_blurred_image_with_text
from utils.prompts import TEXT_CHECK_PROMPT, IMAGE_CHECK_PROMPT, DOCUMENT_CHECK_PROMPT, RECOMMENDATION_PROMPT
from utils.subscription import check_is_subscribed


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
        if await check_is_subscribed(request.user_id):
            to_psy = False
            text = str(request.text)

            if self.psy_handler.active_threads.get(request.user_id):
                to_psy = True

            if request.file is not None:
                if request.file.file_type == 'image':
                    if await UserRequestHandler.is_image_mental(request.file):
                        to_psy = True
                elif request.file.file_type == 'voice':
                    text += '\n'
                    text += await UserRequestHandler.get_transcription(request.file)
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
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы общаться с 🤖 <i>универсальным ассистентом</i> — оформи <b>подписку</b>"
                    )
            else:
                if request.file.file_type == 'image':
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы я смог считывать твои 🌇 <i>фотографии</i> — оформи <b>подписку</b>"
                    )
                elif request.file.file_type == 'voice':
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы я смог считывать твои 🎙️ <i>голосовые сообщения</i> — оформи <b>подписку</b>"
                    )
                elif request.file.file_type == 'document':
                    await main_bot.send_message(
                        request.user_id,
                        "Чтобы я смог считывать твои 📁 <i>файлы</i> — оформи <b>подписку</b>"
                    )

    @staticmethod
    async def is_text_mental(text: str):
        try:
            response = await openAI_client.responses.create(
                model=BASIC_MODEL,
                input=TEXT_CHECK_PROMPT.format(text=text),
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
                file=(voice.filename, voice.file_bytes)
            )
            return transcript.text

        except openai.BadRequestError:
            return ""


class AIHandler:
    assistant_id: str

    def __init__(self):
        self.active_threads = {}
        self.assistant = openAI_client.beta.assistants.retrieve(self.assistant_id)

    async def handle(self, request: UserRequest):
        if self.active_threads.get(request.user_id):
            thread = await openAI_client.beta.threads.retrieve(self.active_threads[request.user_id])
        else:
            thread = await openAI_client.beta.threads.create()
            self.active_threads[request.user_id] = thread.id


        await wait_for_run_completion(thread.id)

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
                    file=("document.pdf", request.file.file_bytes),
                    purpose="assistants"
                )

                if not content:
                    content = "Опиши файл"

                attachments = [{
                    "file_id": document_file.id,
                    "tools": [{"type": "file_search"}]
                }]

        if not content:
            content = "Расскажи о себе"

        await openAI_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=content,
            attachments=attachments
        )

        run = await openAI_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )

        if run.status == 'completed':
            messages = await openAI_client.beta.threads.messages.list(
                thread_id=thread.id,
                run_id=run.id  # Получить сообщения только из этого Run
            )
            await main_bot.send_message(
                request.user_id,
                messages.data[0].content[0].text.value
            )


    async def exit(self, user_id: int):
        if self.active_threads.get(user_id):
            await openAI_client.beta.threads.delete(self.active_threads[user_id])
            self.active_threads[user_id] = None



class PsyHandler(AIHandler):
    assistant_id = mental_assistant_id
    messages_count = {}
    MESSAGES_LIMIT = 10

    async def handle(self, request: UserRequest):
        if not self.messages_count.get(request.user_id):
            await main_bot.send_message(
                request.user_id,
                "Теперь я говорю как психолог. Чтобы выйти, нажмите /menu"
            )
            await user_request_handler.general_handler.exit(request.user_id)
            self.messages_count[request.user_id] = 0
        self.messages_count[request.user_id] += 1

        if self.messages_count[request.user_id] <= self.MESSAGES_LIMIT or await check_is_subscribed(request.user_id):
            await super().handle(request)
        else:
            await self.provide_recommendations(request.user_id)



    async def provide_recommendations(self, user_id: int):
        user = await users_repository.get_user_by_user_id(user_id)
        is_subscribed = await check_is_subscribed(user_id)

        if self.active_threads.get(user_id):
            thread = await openAI_client.beta.threads.retrieve(self.active_threads[user_id])

            await openAI_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=RECOMMENDATION_PROMPT,
            )

            run = await openAI_client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )

            if run.status == 'completed':
                messages = await openAI_client.beta.threads.messages.list(
                    thread_id=thread.id,
                    run_id=run.id  # Получить сообщения только из этого Run
                )

                recommendation = messages.data[0].content[0].text.value


                if not user.used_free_recommendation or is_subscribed:
                    await main_bot.send_message(
                        user_id,
                        recommendation
                    ) # Дать рекомендации
                    response = await openAI_client.audio.speech.create(
                        model=TTS_MODEL,
                        voice="alloy",  # Выберите один из голосов: alloy, echo, fable, onyx, nova, shimmer
                        input=recommendation,
                        response_format="opus"  # mp3, opus, aac, flac, wav, pcm
                    )
                    with tempfile.NamedTemporaryFile(mode="w+", suffix=".ogg") as voice_file:
                        response.stream_to_file(voice_file.name)
                        await main_bot.send_voice(
                            user_id,
                            FSInputFile(voice_file.name)
                        )

                    if not is_subscribed:
                        await users_repository.used_free_recommendation(user_id)

                else:
                    photo_recommendation = generate_blurred_image_with_text(text=recommendation, enable_blur=True)
                    await main_bot.send_photo(
                        user_id,
                        photo=BufferedInputFile(file=photo_recommendation, filename=f"recommendation.png"),
                        caption="🌰<i>Рекомендация</i> готова, но чтобы получить её, нужна <b>подписка</b>",
                        reply_markup=get_rec_keyboard(mode_id=0, mode_type="fast_help").as_markup())

        await self.exit(user_id)

    async def exit(self, user_id: int):
        await super().exit(user_id)
        self.messages_count[user_id] = 0


class GeneralHandler(AIHandler):
    assistant_id = standard_assistant_id


user_request_handler = UserRequestHandler()