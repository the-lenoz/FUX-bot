import calendar
import io
from datetime import datetime, timezone, date

import telegramify_markdown
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, Message
from telegramify_markdown import InterpreterChain, TextInterpreter, FileInterpreter, MermaidInterpreter, ContentTypes

from bots import main_bot
from data.keyboards import buy_sub_keyboard, main_keyboard, keyboard_for_pay, generate_sub_keyboard, \
    generate_change_plan_keyboard
from db.repository import users_repository, user_counters_repository, operation_repository
from settings import messages_dict, menu_photo, sub_description_photo_before, premium_sub_photo
from utils.gpt_client import LLMProvider, ADVANCED_MODEL
from utils.payment_for_services import create_payment
from utils.prompts import TRACKING_REPORT_COMMENT_PROMPT
from utils.subscription import get_user_subscription
from utils.user_request_types import UserFile


async def send_message_copy(user_id, message: Message):
    if message.photo:
        file_buffer = io.BytesIO()
        try:
            await message.bot.download(message.photo, destination=file_buffer)
        except TelegramBadRequest:
            await message.answer(
                "<b>Фото</b> слишком большое - размер не должен превышать <i>20MB</i>"
            )
            return
        file_buffer.seek(0)
        data = file_buffer.read()
        await main_bot.send_photo(user_id, photo=BufferedInputFile(data, "picture.jpg"), caption=message.caption)
    elif message.voice:
        file_buffer = io.BytesIO()
        try:
            await message.bot.download(message.voice, destination=file_buffer)
        except TelegramBadRequest:
            await message.answer(
                "<b>Голосовое</b> слишком большое - размер не должен превышать <i>20MB</i>"
            )
            return
        file_buffer.seek(0)
        data = file_buffer.read()
        await main_bot.send_voice(user_id, voice=BufferedInputFile(data, "voice.ogg"), caption=message.caption)
    elif message.document:
        file_buffer = io.BytesIO()
        try:
            await message.bot.download(message.document, destination=file_buffer)
        except TelegramBadRequest:
            await message.answer(
                "<b>Документ</b> слишком большой - размер не должен превышать <i>20MB</i>"
            )
            return
        file_buffer.seek(0)
        data = file_buffer.read()
        await main_bot.send_voice(user_id, voice=BufferedInputFile(data, message.document.file_name), caption=message.caption)
        await main_bot.send_document(user_id, document=message.document)
    elif message.text:
        await main_bot.send_message(user_id, text=message.text)
    else:
        print("Error sending message: unknown type")


async def send_main_menu(user_id: int):
    user = await users_repository.get_user_by_user_id(user_id)
    text = messages_dict["main_menu_text"] # + str(user.power_mode_days) # TODO RETURN NUTS (messages.json)
    keyboard = await main_keyboard(user_id=user_id)
    await main_bot.send_photo(chat_id=user_id,
                              photo=menu_photo,
                              caption=text,
                              reply_markup=keyboard.as_markup())

async def send_invoice(user_id: int, amount: str, days: str, mode_type: str):
    user = await users_repository.get_user_by_user_id(user_id)
    payment = await create_payment(user.email, amount=amount)
    await operation_repository.add_operation(operation_id=payment[0], user_id=user_id, is_paid=False,
                                             url=payment[1])
    operation = await operation_repository.get_operation_by_operation_id(payment[0])
    keyboard = await keyboard_for_pay(operation_id=operation.id, url=payment[1],
                                      time_limit=int(days), mode_type=mode_type)
    await main_bot.send_message(
        user_id,
        text=f'Оплати счёт в {amount} рублей.\n\nПосле проведения платежа нажми на кнопку "Оплата произведена",'
             ' чтобы подтвердить платеж', reply_markup=keyboard.as_markup())

async def send_subscription_end_message(user_id: int):
    user = await users_repository.get_user_by_user_id(user_id)
    user_counters = await user_counters_repository.get_user_counters(user_id)
    used_time = datetime.now(timezone.utc) - user.creation_date.replace(tzinfo=None)

    if used_time.days % 10 == 1:
        days_str = "день"
    elif used_time.days % 10 in (2, 3, 4):
        days_str = "дня"
    else:
        days_str = "дней"
    if used_time.days in (11, 12, 13, 14):
        days_str = "дней"

    if user_counters.messages_count % 10 == 1:
        messages_str = "сообщение"
    elif user_counters.messages_count % 10 in (2, 3, 4):
        messages_str = "сообщения"
    else:
        messages_str = "сообщений"
    if user_counters.messages_count in (11, 12, 13, 14):
        messages_str = "сообщений"

    if user_counters.emotions_tracks_count % 10 == 1:
        emotions_str = "раз"
    elif user_counters.emotions_tracks_count % 10 in (2, 3, 4):
        emotions_str = "раза"
    else:
        emotions_str = "раз"
    if user_counters.emotions_tracks_count in (11, 12, 13, 14):
        emotions_str = "раз"

    if user_counters.productivity_tracks_count % 10 == 1:
        productivity_str = "раз"
    elif user_counters.productivity_tracks_count % 10 in (2, 3, 4):
        productivity_str = "раза"
    else:
        productivity_str = "раз"
    if user_counters.productivity_tracks_count in (11, 12, 13, 14):
        productivity_str = "раз"

    if user_counters.used_exercises % 10 == 1:
        exercises_str = "упражнение"
    elif user_counters.used_exercises % 10 in (2, 3, 4):
        exercises_str = "упражнения"
    else:
        exercises_str = "упражнений"
    if user_counters.used_exercises in (11, 12, 13, 14):
        exercises_str = "упражнений"

    if user_counters.recommendations_count % 10 == 1:
        recommendations_str = "рекомендацию"
    elif user_counters.recommendations_count % 10 in (2, 3, 4):
        recommendations_str = "рекомендации"
    else:
        recommendations_str = "рекомендаций"
    if user_counters.recommendations_count in (11, 12, 13, 14):
        recommendations_str = "рекомендаций"

    await main_bot.send_photo(
        caption="К сожалению, твоя подписка закончилась.\n"
                f"Мы вместе работали над твоим ментальным здоровьем <b>{used_time.days}</b> {days_str}.\n"
                "За это время ты:\n"
                f"1. <i>Написал мне <b>{user_counters.messages_count}</b> {messages_str}</i>\n"
                f"2. <i>Отследил свои эмоции <b>{user_counters.emotions_tracks_count}</b> {emotions_str}</i>\n"
                f"3. <i>Отследил свою продуктивность <b>{user_counters.productivity_tracks_count}</b> {productivity_str}</i>\n"
                f"4. <i>Получил <b>{user_counters.recommendations_count}</b> {recommendations_str} для решения проблем</i>\n"
                f"5. <i>Получил <b>{user_counters.used_exercises}</b> {exercises_str} для самопомощи</i>\n\n"
                "Надеюсь, я был для тебя полезен!\n"
                "Ты всегда можешь продлить подписку, если захочешь",
        photo=sub_description_photo_before,
        chat_id=user_id,
        reply_markup=buy_sub_keyboard.as_markup())

async def send_motivation_weekly_message(user_id: int):
    # Получаем сегодняшнюю дату
    today = datetime.today().date()

    # Находим последний день текущего месяца
    last_day_of_month = calendar.monthrange(today.year, today.month)[1]

    # Создаем объект date для последнего дня месяца
    last_day_date = date(today.year, today.month, last_day_of_month)

    # Вычисляем количество оставшихся дней
    remaining_days = (last_day_date - today).days

    # Рассчитываем количество недель и округляем
    weeks_left = round(remaining_days / 7)

    if weeks_left == 1:
        remaining_str = "1 неделю"
    elif weeks_left == 2:
        remaining_str = "2 недели"
    elif weeks_left == 3:
        remaining_str = "3 недели"
    elif weeks_left == 4:
        remaining_str = "4 недели"
    else:
        return

    await main_bot.send_message(
        user_id,
        messages_dict["tracking_weekly_motivation_message"].format(remaining_str)
    )

async def send_monthly_tracking_report_comment(user_id: int, report_image_bytes: bytes):
    messages = [LLMProvider.create_message(
        [
            await LLMProvider.create_image_content_item(UserFile(
                file_bytes=report_image_bytes,
                filename="report.png",
                file_type="image"
            ))
        ]
    ), LLMProvider.create_message(
        [
            await LLMProvider.create_text_content_item(TRACKING_REPORT_COMMENT_PROMPT)
        ]
    )]
    interpreter_chain = InterpreterChain([
        TextInterpreter(),  # Use pure text first
        FileInterpreter(),  # Handle code blocks
        MermaidInterpreter(session=None),  # Handle Mermaid charts
    ])
    comment = await LLMProvider(ADVANCED_MODEL).process_request(messages)

    boxs = await telegramify_markdown.telegramify(
        content=comment,
        interpreters_use=interpreter_chain,
        latex_escape=True,
        normalize_whitespace=True,
        max_word_count=4090  # The maximum number of words in a single message.
    )

    for item in boxs:
        if item.content_type == ContentTypes.TEXT:
            await main_bot.send_message(
                user_id,
                item.content,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        elif item.content_type == ContentTypes.PHOTO:
            await main_bot.send_photo(
                user_id,
                BufferedInputFile(file=item.file_data, filename=item.file_name),
                caption=item.caption,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        elif item.content_type == ContentTypes.FILE:
            await main_bot.send_document(
                user_id,
                BufferedInputFile(file=item.file_data, filename=item.file_name),
                caption=item.caption,
                parse_mode=ParseMode.MARKDOWN_V2
            )


async def send_subscription_management_menu(user_id: int):
    sub = await get_user_subscription(user_id)
    if bool(sub):
        if sub.recurrent:
            await main_bot.send_photo(user_id,
                                      caption=messages_dict["your_paid_sub_photo_description"],
                                      photo=premium_sub_photo,
                                      reply_markup=(await generate_change_plan_keyboard(user_id, sub.plan)).as_markup())
        else:
            await main_bot.send_photo(user_id,
                                  caption=messages_dict["your_free_sub_photo_description"],
                                  photo=premium_sub_photo,
                                  reply_markup=(await generate_sub_keyboard(user_id)).as_markup())
    else:
        await main_bot.send_photo(user_id,
                                  caption=messages_dict["buy_sub_photo_description"],
                                  photo=premium_sub_photo,
                                  reply_markup=(await generate_sub_keyboard(user_id)).as_markup())
