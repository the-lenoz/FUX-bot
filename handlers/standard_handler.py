import io

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

# from data.keyboards import choice_keyboard
# from data.messages import start_message, wait_manager, update_language
from utils.gpt_distributor import user_request_handler
from utils.user_request_types import UserFile, UserRequest

standard_router = Router()


@standard_router.callback_query(F.data == "start_problem_conversation")
async def start_problem_conversation(call: CallbackQuery, state: FSMContext, bot: Bot):
    request = UserRequest(
        user_id=call.from_user.id,
        text="Привет"
    )
    await call.message.delete()
    await user_request_handler.handle(request)


@standard_router.message(Command("recommendation"))
async def provide_recommendation(message: Message, bot: Bot):
    await user_request_handler.AI_handler.provide_recommendations(message.from_user.id)


@standard_router.message(F.text)
async def standard_message_handler(message: Message, bot: Bot):
    try:
        await bot.send_chat_action(chat_id=message.from_user.id, action="typing")
    except TelegramRetryAfter:
        pass

    request = UserRequest(
        user_id=message.from_user.id,
        text=message.text
    )

    await user_request_handler.handle(request)


@standard_router.message(F.photo)
async def standard_message_photo_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    try:
        await bot.send_chat_action(chat_id=message.from_user.id, action="typing")
    except TelegramRetryAfter:
        pass
    file_buffer = io.BytesIO()
    try:
        await bot.download(message.photo[-1], destination=file_buffer)
    except TelegramBadRequest:
        await message.answer(
            "<b>Картинка</b> слишком большая - размер не должен превышать <i>20MB</i>"
        )
        return
    file_buffer.seek(0)
    data = file_buffer.read()

    file = UserFile(
        file_bytes=data,
        file_type="image",
        filename="image.jpg"
    )

    request = UserRequest(
        user_id=user_id,
        text=message.caption,
        file=file
    )

    await user_request_handler.handle(request)


@standard_router.message(F.voice)
async def standard_message_voice_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    try:
        await bot.send_chat_action(chat_id=message.from_user.id, action="typing")
    except TelegramRetryAfter:
        pass
    file_buffer = io.BytesIO()
    try:
        await bot.download(message.voice, destination=file_buffer)
    except TelegramBadRequest:
        await message.answer(
            "<b>Голосовое сообщение</b> слишком большое - размер не должен превышать <i>20MB</i>"
        )
        return
    file_buffer.seek(0)
    data = file_buffer.read()

    file = UserFile(
        file_bytes=data,
        file_type="voice",
        filename="voice.ogg"
    )

    request = UserRequest(
        user_id=user_id,
        text=message.caption,
        file=file
    )

    await user_request_handler.handle(request)

@standard_router.message(F.document)
async def standard_message_document_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    try:
        await bot.send_chat_action(chat_id=message.from_user.id, action="typing")
    except TelegramRetryAfter:
        pass
    file_buffer = io.BytesIO()
    try:
        await bot.download(message.document, destination=file_buffer)
    except TelegramBadRequest:
        await message.answer(
            "<b>Документ</b> слишком большой - размер не должен превышать <i>20MB</i>"
        )
        return
    file_buffer.seek(0)
    data = file_buffer.read()

    filename_suffix = message.document.file_name.split('.')[-1]
    if filename_suffix in ('png', 'jpg', 'jpeg', 'webp', 'gif'):
        file = UserFile(
            file_bytes=data,
            file_type="image",
            filename=message.document.file_name
        )
    else:
        file = UserFile(
            file_bytes=data,
            file_type="document",
            filename=message.document.file_name
        )

    request = UserRequest(
        user_id=user_id,
        text=message.caption,
        file=file
    )

    await user_request_handler.handle(request)


@standard_router.message(F.video_note)
async def standard_message_video_note_handler(message: Message, bot: Bot):
    await message.answer(
        "К сожалению, я пока не умею смотреть <b>видеосообщения</b>"
    )
