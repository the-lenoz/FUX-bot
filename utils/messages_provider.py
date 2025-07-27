import calendar
from datetime import datetime, timezone, date

from bots import main_bot
from data.keyboards import buy_sub_keyboard
from db.repository import users_repository, user_counters_repository
from settings import payment_photo, messages_dict


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
        photo=payment_photo,
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
