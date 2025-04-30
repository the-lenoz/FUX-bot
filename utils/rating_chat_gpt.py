import io
import traceback
from os import getenv

import aiohttp
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from db.repository import users_repository

load_dotenv(find_dotenv("../.env"))
api_key = getenv("GPT_TOKEN")
mental_assistant_id = getenv("MENTAL_ASSISTANT_ID")
standard_assistant_id = getenv("STANDARD_ASSISTANT_ID")

class GPT:
    def __init__(self, assistant_id: str | None = mental_assistant_id, thread_id: str | None = None):
        if assistant_id == "standard":
            self.assistant_id = standard_assistant_id
            self.assistant_type = "standard"
        else:
            self.assistant_id = mental_assistant_id
            self.assistant_type = "mental"
        self.client = OpenAI(api_key=api_key)
        self.assistant = self.client.beta.assistants.retrieve(assistant_id=self.assistant_id)
        self.thread_id = thread_id

    async def update_thread_id(self, user_id: int, type_assistant : str | None = "mental"):
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
        if self.assistant_id == standard_assistant_id:
            await users_repository.update_standard_ai_threat_id_by_user_id(user_id=user_id, thread_id=self.thread_id)
        else:
            await users_repository.update_mental_ai_threat_id_by_user_id(user_id=user_id, thread_id=self.thread_id)
        return thread

    async def send_message(self, user_id, with_audio_transcription: bool = False, text: str | None = None, image_bytes=None,
                           document_bytes=None,
                           document_type: str | None = None,
                           audio_bytes: bytes | None = None,
                           temperature: float | None = 1.0,
                           name: str | None = None,
                           gender: str | None = None,
                           age: str | None = None):
        # try:
        have_info = False
        about_user: str = ""
        if name is not None or name == "NoName":
            about_user += f"\nИмя: {name}\n"
            have_info = True
        if gender is not None:
            about_user += f"\nПол: {gender}\n"
            have_info = True
        if age is not None:
            about_user += f"\nДиапозон возраста: {age}\n"
            have_info = True
        if temperature == 0.7:
            about_user += "\nОБЩАЙСЯ С ДАННЫМ ПОЛЬЗОВАТЕЛЕМ МАКСИМАЛЬНО ПРЯМОЛИНЕЙНО БЕЗ ОСОБОЙ МЯГКОСТИ"
            have_info = True
        elif temperature == 1.3:
            about_user += "\nОБЩАЙСЯ С ДАННЫМ ПОЛЬЗОВАТЕЛЕМ МАКСИМАЛЬНО МЯГКО И ОСТОРОЖНО"
            have_info = True
        if have_info:
            about_user = ("Отвечай с учетом следующей информации о пользователе(используй разные конструкции обращения"
                          " к пользорвателю, например,  иногда по имени, иногда просто по местоимению) Если ты видишь,"
                          " что в предыдущем сообщении ты обращался по имени, то сейчас по имени не обращайся, а также"
                          " не надо каждый раз приветствовать\n\n") + about_user
        if text is None:
            text = ""
        if len(about_user) > 0:
            text = about_user + text
        if self.thread_id is None:
            thread = await self.update_thread_id(user_id=user_id)
        else:
            thread = self.client.beta.threads.retrieve(thread_id=self.thread_id)
        if text is None and image_bytes is None:
            return None
        elif image_bytes is None and audio_bytes is None:
            content = [{
                        "type": "text",
                        "text": text
                    }]
        else:
            if image_bytes is not None:
                image_bytes.seek(0)
                image_file = self.client.files.create(
                    file=("image.png", image_bytes),
                    purpose="vision"
                )
                content = [
                    {
                        "type": "text",
                        "text": text
                    },
                    {
                        "type": "image_file",
                        "image_file": {"file_id": image_file.id}
                    }
                ]
            else:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bytes
                )
                content = [
                    {
                        "type": "text",
                        "text": transcript.text
                    }
                ]
        attachments = []
        if document_bytes is not None:
            document_bytes.seek(0)
            document_file = self.client.files.create(
                file=(f"document.{document_type}", document_bytes),
                purpose="assistants"
            )
            attachments.append({
                    "file_id": document_file.id,
                    "tools": [{"type": "file_search"}]
            })
            # content.append({
            #             "type": "file",
            #             "file": {"file_id": document_file.id}
            #         })
        try:
            thread_message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=content,
                attachments=attachments,
                timeout=15.0
            )
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=self.assistant.id,
                temperature=temperature,
                timeout=15.0
            )
            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                message_text = messages.data[0].content[0].text.value.replace("**", "").replace('"', "'").replace("#", "")
                if with_audio_transcription:
                    audio_data = await self.generate_audio_by_text(text=message_text)
                    return message_text, audio_data
                return message_text

            else:
                # print("\n" * 4)
                # print(run.status)
                # print(run.json())
                # print("\n" * 4)
                return "Произошла непредвиденная ошибка, попробуй еще раз!"
        except Exception as e:
            print("\n" * 4)
            full_error = traceback.format_exc()
            # print(f"Ошибка в ебаном джипити как он меня заебал\n\n{full_error}")
            # print("\n" * 4)
        # except:
        #     return "Произошла непредвиденная ошибка, попробуй еще раз!"
        #     print(traceback.format_exc())

    @staticmethod
    async def generate_audio_by_text(text: str) -> io.BytesIO:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Оборачиваем текст в SSML, чтобы задать скорость 1.25 (125%)

        payload = {
            "model": "gpt-4o-mini-tts",
            "input": text,
            "voice": "shimmer",
            "instructions": "Speak dramatic",
            "response_format": "mp3"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return io.BytesIO(audio_data)
                else:
                    error_text = await response.text()
                    raise Exception(f"Ошибка при генерации речи: {response.status}\n{error_text}")

    @staticmethod
    async def transcribe_audio(audio_bytes, language='ru'):
        """
        Преобразует аудио в формате MP3 в текст с помощью API OpenAI.

        :param audio_bytes: Аудио в байтовом формате.
        :param api_key: Ваш API-ключ OpenAI.
        :param language: Язык аудио для транскрибации (по умолчанию 'ru' для русского).
        :return: Расшифрованный текст.
        """
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        # Создаем объект файла из байтового аудио
        audio_file = audio_bytes
        audio_file.name = 'audio.mp3'

        # Отправляем запрос на транскрибацию
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data={
                'file': audio_file,
                'model': 'whisper-1',
                'language': language
            }) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('text', '')
                else:
                    error_text = await response.text()
                    raise Exception(f"Ошибка при транскрибации: {response.status}\n{error_text}")



