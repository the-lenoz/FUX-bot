import datetime
import traceback
from datetime import timezone

from aiogram import Bot

import utils.checkups
from data.keyboards import buy_sub_keyboard, notification_keyboard, main_keyboard
from db.repository import subscriptions_repository, users_repository, checkup_repository, events_repository, \
    admin_repository, limits_repository
from settings import payment_photo, how_are_you_photo, menu_photo
from utils.checkup_stat import send_weekly_checkup_report, send_monthly_checkup_report
from utils.gpt_distributor import user_request_handler
from utils.messages_provider import send_subscription_end_message


async def edit_activation_sub(main_bot: Bot):
    subs = await subscriptions_repository.select_all_active_subscriptions()
    now_date = datetime.datetime.now(datetime.timezone.utc)
    for sub in subs:
        if now_date - sub.creation_date >= datetime.timedelta(hours=24 * sub.time_limit_subscription):
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
        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {checkup.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue

async def send_recommendations(main_bot: Bot):
    users = await users_repository.select_all_users()
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)  # Можно использовать локальное время, если требуется

    for user in users:
        last_event = await events_repository.get_last_event_by_user_id(user_id=user.user_id)
        if user_request_handler.AI_handler.active_threads.get(user.user_id) \
                and now - last_event.creation_date >= datetime.timedelta(minutes=120):
            if user.notified_with_recommendation < 3 \
                    and user_request_handler.AI_handler.messages_count.get(user.user_id) \
                    and user_request_handler.AI_handler.messages_count.get(user.user_id) >= 6 \
                    and user_request_handler.AI_handler.check_is_dialog_psy(user.user_id):
                await user_request_handler.AI_handler.provide_recommendations(user.user_id, from_notification=True)
            else:
                text = "✍️<i>Для общения - просто </i><b>пиши</b><i>, ничего выбирать не надо</i>"
                keyboard = await main_keyboard(user_id=user.user_id)
                await main_bot.send_photo(chat_id=user.user_id,
                                          photo=menu_photo,
                                          caption=text,
                                          reply_markup=keyboard.as_markup())
                await user_request_handler.AI_handler.exit(user.user_id)


async def notification_reminder(main_bot: Bot):
    users = await users_repository.select_all_users()
    now = datetime.datetime.now(timezone.utc)  # Можно использовать локальное время, если требуется

    for user in users:
        last_event = await events_repository.get_last_event_by_user_id(user_id=user.user_id)
        if not last_event:
            # Можно реализовать отдельное поведение для новых пользователей без событий
            continue

        delta = now - last_event.creation_date

        # Если не отправлялось уведомление о дневном пороге и прошло >= 2 дня
        if not last_event.day_notif_sent and delta >= datetime.timedelta(hours=48):
            try:
                await main_bot.send_photo(
                    photo=how_are_you_photo,
                    chat_id=user.user_id,
                    caption="> Добрый день, коллеги\.\.\.\n\n\nВы подготовили отчёт\?📙",
                    parse_mode="MarkdownV2",
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
    now_date = datetime.datetime.now(timezone.utc)
    for user in users:
        try:
            user_active_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user.user_id)
            if user_active_checkups is not None and len(user_active_checkups) > 0:
                max_date = None
                for checkup in user_active_checkups:
                    if max_date is not None and ((now_date - checkup.last_date_send) > datetime.timedelta(hours=24)) \
                            and user.power_mode_days != 0:
                        if checkup.last_date_send.weekday() == 6:
                            await send_weekly_checkup_report(user.user_id, checkup.last_date_send)
                        if (checkup.last_date_send + datetime.timedelta(days=1)).month != checkup.last_date_send.month:
                            await send_monthly_checkup_report(user.user_id, checkup.last_date_send)
                        await users_repository.update_power_mode_days_by_user_id(user_id=user.user_id, new_days=0)
                        await main_bot.send_message(chat_id=user.user_id,
                                                    text="Ох… твои орехи раскололись🌰, но "
                                                         "можно начать трекинг "
                                                        + (
                                                        "эмоций"
                                                        if checkup.type_checkup == "emotions" else "продуктивности") +
                                                         " снова"
                                                    )
        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {user.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue


async def send_user_statistics(admin_bot: Bot):
    admins = await admin_repository.select_all_admins()
    user_stat = await users_repository.get_user_creation_statistics()
    text_message = (f"Количество новых пользователей:\n\n"
                    f"Статистика за день: <b>{user_stat.get('day')}</b>\n"
                    f"Статистика за неделю: <b>{user_stat.get('week')}</b>\n"
                    f"Статистика за месяц: <b>{user_stat.get('month')}</b>\n"
                    f"Статистика за квартал: <b>{user_stat.get('quarter')}</b>\n"
                    f"Статистика за все время <b>{user_stat.get('all_time')}</b>")
    for admin in admins:
        await admin_bot.send_message(
            admin.admin_id,
            text_message
        )


async def reset_limits():
    await limits_repository.reset_all_limits(
        exercises_remaining=2,
        universal_requests_remaining=20
    )



