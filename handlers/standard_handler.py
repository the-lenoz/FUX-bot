import html
import html
import io

from aiogram import Router, F, Bot
from aiogram.types import Message

from data.keyboards import buy_sub_keyboard
# from data.keyboards import choice_keyboard
# from data.messages import start_message, wait_manager, update_language
from db.repository import users_repository, ai_requests_repository, subscriptions_repository
from utils.rating_chat_gpt import GPT

standard_router = Router()


@standard_router.message(F.text)
async def standard_message_handler(message: Message, bot: Bot):
    text = message.text
    user_id = message.from_user.id
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user is not None and user.full_registration:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if user_sub is None:
            await message.answer("Чтобы общаться со стандартным GPT у тебя должна быть подписка",
                                 reply_markup=buy_sub_keyboard.as_markup())
            return
        # delete_message = await message.reply("Формулирую ответ, это займет не более 5 секунд")
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        ai_answer = await GPT(thread_id=user.standard_ai_threat_id, assistant_id="standard").send_message(user_id=user_id,
                                                                                 text=text,
                                                                                 temperature=1,
                                                                                 name=user.name,
                                                                                 age=user.age,
                                                                                 gender=user.gender)
        ai_answer = html.escape(ai_answer)
        await message.reply(text=ai_answer)
        await ai_requests_repository.add_request(user_id=message.from_user.id,
                                                 has_photo=False,
                                                 answer_ai=ai_answer,
                                                 user_question=message.text)
        # await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)


@standard_router.message(F.photo)
async def standard_message_photo_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user is not None and user.full_registration:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if user_sub is None:
            await message.answer("Чтобы общаться со стандартным GPT у тебя должна быть подписка",
                                 reply_markup=buy_sub_keyboard.as_markup())
            return
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        # delete_message = await message.reply("Формулирую ответ, это займет не более 5 секунд")
        text = message.caption
        photo_bytes_io = io.BytesIO()
        photo_id = message.photo[-1].file_id
        print(photo_id)
        await bot.download(message.photo[-1], destination=photo_bytes_io)
        ai_answer = await GPT(thread_id=user.standard_ai_threat_id, assistant_id="standard").send_message(user_id=user_id,
                                                                                                        text=text,
                                                                                                        temperature=1,
                                                                                                        name=user.name,
                                                                                                        age=user.age,
                                                                                                        gender=user.gender,
                                                                                                        image_bytes=photo_bytes_io)
        await message.reply(text=ai_answer)
        await ai_requests_repository.add_request(user_id=message.from_user.id,
                                                 has_photo=True,
                                                 photo_id=photo_id,
                                                 answer_ai=ai_answer,
                                                 user_question=text if text is not None else "")
        # await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)


@standard_router.message(F.voice)
async def standard_message_voice_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user is not None and user.full_registration:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if user_sub is None:
            await message.answer("Чтобы общаться со стандартным GPT у тебя должна быть подписка",
                                 reply_markup=buy_sub_keyboard.as_markup())
            return
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        audio_bytes_io = io.BytesIO()
        message_voice_id = message.voice.file_id
        await bot.download(message_voice_id, destination=audio_bytes_io)
        transcribed_audio_text = await GPT(thread_id=user.standard_ai_threat_id, assistant_id="standard").transcribe_audio(audio_bytes=audio_bytes_io,)
        # print(transcribed_audio_text)
        ai_answer = await GPT(thread_id=user.standard_ai_threat_id, assistant_id="standard").send_message(
            user_id=user_id,
            text=transcribed_audio_text,
            temperature=1,
            name=user.name,
            age=user.age,
            gender=user.gender)
        ai_answer = html.escape(ai_answer)
        await message.reply(text=ai_answer)
        await ai_requests_repository.add_request(user_id=message.from_user.id,
                                                 has_photo=False,
                                                 answer_ai=ai_answer,
                                                 user_question=message.text)

@standard_router.message(F.document)
async def standard_message_document_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await users_repository.get_user_by_user_id(user_id=user_id)
    if user is not None and user.full_registration:
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user_id)
        if user_sub is None:
            await message.answer("Чтобы общаться со стандартным GPT у тебя должна быть подписка",
                                 reply_markup=buy_sub_keyboard.as_markup())
            return
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        # delete_message = await message.reply("Формулирую ответ, это займет не более 5 секунд")
        text = message.caption
        file_buffer = io.BytesIO()
        # Скачиваем файл в BytesIO
        await bot.download(message.document, destination=file_buffer)
        if message.document.file_name:
            # Получаем расширение из имени файла
            extension = message.document.file_name.split('.')[-1].lower()
            ai_answer = await GPT(thread_id=user.standard_ai_threat_id, assistant_id="standard").send_message(user_id=user_id,
                                                                                                            text=text,
                                                                                                            temperature=1,
                                                                                                            name=user.name,
                                                                                                            age=user.age,
                                                                                                            gender=user.gender,
                                                                                                            document_bytes=file_buffer,
                                                                                                            document_type=extension)
            await message.reply(text=ai_answer)
            await ai_requests_repository.add_request(user_id=message.from_user.id,
                                                     has_photo=False,
                                                     answer_ai=ai_answer,
                                                     user_question=text if text is not None else "",
                                                     has_files=True,
                                                     file_id=message.document.file_id)
        # await bot.delete_message(message_id=delete_message.message_id, chat_id=user_id)

