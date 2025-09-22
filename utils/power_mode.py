import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots import main_bot
from data.keyboards import nuts_description_keyboard
from db.repository import user_counters_repository, events_repository, user_timezone_repository, users_repository, \
    subscriptions_repository
from settings import MAX_DAYS_FREEZE, DEFAULT_TIMEZONE
from data.message_templates import messages_dict


async def trigger_power_mode(user_id: int):
    last_user_event = await events_repository.get_last_event_by_user_id(user_id)
    user_timezone = await user_timezone_repository.get_user_timezone_delta(user_id) or DEFAULT_TIMEZONE

    now_date = datetime.datetime.now(datetime.timezone(user_timezone)).date()
    user = await users_repository.get_user_by_user_id(user_id)

    if not last_user_event or last_user_event.upd_date.date() != now_date or user.power_mode_days == 0:
        await update_power_mode(user_id)

async def interval_skip_trigger(user_id: int):
    last_user_event = await events_repository.get_last_event_by_user_id(user_id)
    user_timezone = await user_timezone_repository.get_user_timezone_delta(user_id) or DEFAULT_TIMEZONE

    now_date = datetime.datetime.now(datetime.timezone(user_timezone)).date()
    yesterday_date = (datetime.datetime.now(datetime.timezone(user_timezone)) - datetime.timedelta(days=1)).date()

    if (last_user_event and last_user_event.upd_date.date() != now_date
            and last_user_event.creation_date.date() != yesterday_date):
        await trigger_skipped_day(user_id)

async def update_power_mode(user_id: int):
    user = await users_repository.get_user_by_user_id(user_id)
    if user.power_mode_days:
        await main_bot.send_message(
            user_id,
            messages_dict["new_nut_format"].format(user.power_mode_days + 1),
            reply_markup=nuts_description_keyboard.as_markup()
        )

    await users_repository.update_power_mode_days_by_user_id(user_id, user.power_mode_days + 1)

async def trigger_skipped_day(user_id: int):
    await user_counters_repository.user_skipped_day(user_id)
    user_counters = await user_counters_repository.get_user_counters(user_id)
    if user_counters.skipped_days > MAX_DAYS_FREEZE:
        await break_power_mode(user_id)
    last_user_event = await events_repository.get_last_event_by_user_id(user_id)
    await events_repository.update_event(last_user_event)

async def break_power_mode(user_id: int):
    user = await users_repository.get_user_by_user_id(user_id)
    if user.power_mode_days:
        await users_repository.update_power_mode_days_by_user_id(user_id, 0)
        user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id)
        await main_bot.send_message(
            user_id,
            messages_dict["break_power_mode"],
            reply_markup=nuts_description_keyboard.as_markup()
        )
