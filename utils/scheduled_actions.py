import datetime
import traceback
from datetime import timezone

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

import utils.checkups
from data.keyboards import buy_sub_keyboard, notification_keyboard, main_keyboard
from db.repository import subscriptions_repository, users_repository, checkup_repository, events_repository, \
    admin_repository, limits_repository, days_checkups_repository, user_timezone_repository, user_counters_repository
from settings import payment_photo, how_are_you_photo, menu_photo, messages_dict

from utils.gpt_distributor import user_request_handler
from utils.messages_provider import send_subscription_end_message, send_main_menu
from utils.power_mode import interval_skip_trigger
from utils.statistics import generate_statistics_text


async def edit_activation_sub(main_bot: Bot):
    subs = await subscriptions_repository.select_all_active_subscriptions()
    now_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    for sub in subs:
        if now_date - sub.creation_date.replace(tzinfo=None) >= datetime.timedelta(hours=24 * sub.time_limit_subscription):
            try:
                await subscriptions_repository.deactivate_subscription(sub.id)
                await send_subscription_end_message(sub.user_id)
            except Exception as e:
                print(e)
                continue
        elif (now_date - sub.creation_date >= datetime.timedelta(hours=24 * (sub.time_limit_subscription - 3))) and not sub.send_notification:
            try:
                await subscriptions_repository.update_send_notification_subscription(subscription_id=sub.id)
                await main_bot.send_photo(
                    caption="Твоя подписка закончится через 3 дня. Ты можешь продлить её:",
                    photo=payment_photo,
                    chat_id=sub.user_id,
                    reply_markup=buy_sub_keyboard.as_markup())
            except Exception as e:
                print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {sub.user_id}" + traceback.format_exc() + "\n\n")

async def send_checkup():
    checkups = await checkup_repository.select_all_active_checkups()
    now_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    for checkup in checkups:
        try:
            if now_date.time() >= checkup.time_checkup and now_date.date() != checkup.last_date_send.date():
                await utils.checkups.send_checkup(checkup.id)
        except TelegramForbiddenError as e:
            await days_checkups_repository.delete_days_checkups_by_checkup_id(checkup.id)
            await checkup_repository.delete_checkup_by_checkup_id(checkup.id)

        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {checkup.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue

async def send_recommendations(main_bot: Bot):
    users = await users_repository.select_all_users()
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    for user in users:
        user_counters = await user_counters_repository.get_user_counters(user.user_id)
        last_event = await events_repository.get_last_event_by_user_id(user_id=user.user_id)
        if user_request_handler.AI_handler.active_threads.get(user.user_id) \
                and now - last_event.creation_date >= datetime.timedelta(minutes=120):
            if user_counters.notified_with_recommendation < 3 \
                    and user_request_handler.AI_handler.messages_count.get(user.user_id) \
                    and user_request_handler.AI_handler.messages_count.get(user.user_id) >= 6 \
                    and user_request_handler.AI_handler.check_is_dialog_psy(user.user_id):
                await user_request_handler.AI_handler.provide_recommendations(user.user_id, from_notification=True)
                await user_counters_repository.notified_with_recommendation(user.user_id)
            else:
                await send_main_menu(user.user_id)
                await user_request_handler.AI_handler.exit(user.user_id)


async def notification_reminder(main_bot: Bot):
    users = await users_repository.select_all_users()
    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None)  # Можно использовать локальное время, если требуется

    for user in users:
        last_event = await events_repository.get_last_event_by_user_id(user_id=user.user_id)
        if not last_event:
            # Можно реализовать отдельное поведение для новых пользователей без событий
            continue

        delta = now - last_event.creation_date.replace(tzinfo=None)

        # Если не отправлялось уведомление о дневном пороге и прошло >= 2 дня
        if not last_event.day_notif_sent and delta >= datetime.timedelta(hours=48):
            try:
                await main_bot.send_photo(
                    photo=how_are_you_photo,
                    chat_id=user.user_id,
                    caption="> _Давай пообщаемся_ 😌",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=notification_keyboard.as_markup()
                )
                last_event.day_notif_sent = True
                await events_repository.update_event(last_event)
            except Exception as e:
                continue

        # Если дневное уведомление уже отправлено, но еще не отправлено недельное, и прошло >= 7 дней
        elif last_event.day_notif_sent and not last_event.week_notif_sent and delta >= datetime.timedelta(days=7):
            try:
                await main_bot.send_message(
                    user.user_id,
                    "Ты не взаимодействовал со мной уже неделю! Жду тебя снова",
                    reply_markup=notification_keyboard.as_markup()
                )
                last_event.week_notif_sent = True
                await events_repository.update_event(last_event)
            except:
                continue
        # Если недельное уведомление отправлено, но не отправлено уведомление по месячному порогу, и прошло >= 30 дней
        elif last_event.week_notif_sent and not last_event.month_notif_sent and delta >= datetime.timedelta(days=30):
            try:
                await main_bot.send_message(
                    user.user_id,
                    "Ты не взаимодействовал со мной уже месяц! Скучаю и жду тебя снова",
                    reply_markup=notification_keyboard.as_markup()
                )
                last_event.month_notif_sent = True
                await events_repository.update_event(last_event)
            except:
                continue

async def break_power_mode(main_bot: Bot):
    users = await users_repository.select_all_users()
    for user in users:
        try:
            await interval_skip_trigger(user.user_id)
        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {user.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue


async def send_statistics(admin_bot: Bot):
    statistics = await generate_statistics_text()
    admins = await admin_repository.select_all_admins()

    for admin in admins:
        await admin_bot.send_message(
            admin.admin_id,
            statistics
        )


async def reset_limits(main_bot: Bot):
    users = await users_repository.select_all_users()
    for user in users:
        user_timezone_delta = await user_timezone_repository.get_user_timezone_delta(user_id=user.user_id)
        if datetime.datetime.now(timezone(user_timezone_delta)).weekday() == 1 and datetime.datetime.now(timezone(user_timezone_delta)).hour == 8:
            await limits_repository.update_user_limits(
                user_id=user.user_id,
                exercises_remaining=2,
                universal_requests_remaining=10,
                psychological_requests_remaining=30
            )

            user_sub = await subscriptions_repository.get_active_subscription_by_user_id(user_id=user.user_id)
            if user_sub is None:
                try:
                    await main_bot.send_message(chat_id=user.user_id, text=messages_dict["week_quota_message_text"])
                except:
                    continue




