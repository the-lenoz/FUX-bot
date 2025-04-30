import asyncio
import datetime
import traceback


from aiogram import Dispatcher, Bot
from aiogram.types import BufferedInputFile

from data.keyboards import buy_sub_keyboard, emotions_keyboard, productivity_keyboard
from db.engine import DatabaseEngine
from db.repository import subscriptions_repository, users_repository, fast_help_repository, go_deeper_repository, \
    fast_help_dialogs_repository, fast_help_dialog_repository, mental_problems_repository, summary_user_repository, \
    checkup_repository, days_checkups_repository, events_repository
from settings import payment_photo, checkup_emotions_photo, checkup_productivity_photo, how_are_you_photo, emoji_dict, \
    speed_dict

from utils.rating_chat_gpt import GPT
from utils.сheckup_stat import generate_emotion_chart


async def edit_activation_sub(main_bot: Bot):
    # print("хуила")
    subs = await subscriptions_repository.select_all_active_subscriptions()
    now_date = datetime.datetime.now()
    for sub in subs:
        if now_date - sub.creation_date >= datetime.timedelta(hours=24 * sub.time_limit_subscription):
            try:
                await subscriptions_repository.deactivate_subscription(sub.id)
                await main_bot.send_photo(
                    caption="К сожалению, твоя подписка закончена. Необходимо оплатить подписку",
                    photo=payment_photo,
                    chat_id=sub.user_id,
                    reply_markup=buy_sub_keyboard.as_markup())
            except Exception as e:
                print(e)
                continue
        elif (now_date - sub.creation_date >= datetime.timedelta(hours=24 * (sub.time_limit_subscription - 3))) and not sub.send_notification:
            try:
                await subscriptions_repository.update_send_notification_subscription(subscription_id=sub.id)
                await main_bot.send_photo(
                    caption="Твоя подписка закончится через 3 дня",
                    photo=payment_photo,
                    chat_id=sub.user_id,
                    reply_markup=buy_sub_keyboard.as_markup())
            except Exception as e:
                print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {sub.user_id}" + traceback.format_exc() + "\n\n")
                continue


async def send_week_rec(main_bot: Bot):
    users = await users_repository.select_all_users()
    now_date = datetime.datetime.now()
    for user in users:
        try:
            print(user.user_id)
            if (now_date - user.last_rec_week_date) > datetime.timedelta(days=7.0):
                user_summaries = await summary_user_repository.get_summaries_by_user_id(user_id=user.user_id)
                print(user_summaries)
                if user_summaries is not None and len(user_summaries) > 0:
                    user_last_summary = await summary_user_repository.get_summary_by_user_id_and_number_summary(user_id=user.user_id,
                                                                                                                number_summary=len(user_summaries))
                    user_problems = await mental_problems_repository.get_problems_by_summary_id(summary_id=user_last_summary.id)
                    week_rec_promt = f'''Сгенерируй рекомендацию для пользователя на основе контекста данного чата с данным пользователем.
                                       Также при генерации рекомендации сконцентрируйся на следующем словаре, где показывается,
                                         какие проблемы есть, а каких нет у человека\nвот словарь:\n{user_problems}\n
                                            \nВот список проблем, которые указаны в словаре\n
                                            1. Самооценка
                                            2. Эмоции
                                            3. Отношения
                                            4. Любовь 
                                            5. Карьера
                                            6. Финансы
                                            7. Здоровье
                                            8. Самореализация
                                            9. Выгорание
                                            10. Духовность")
                                            Начни со слова "Рекомендация недели:". В твоем ответе 
                                            должны быть только рекомендации и никакого второстепенного текста'''
                    ai_rec = await GPT(thread_id=user.mental_ai_threat_id).send_message(user_id=user.user_id,
                                                                               temperature=user.ai_temperature,
                                                                               name=user.name,
                                                                               gender=user.gender,
                                                                               age=user.age,
                                                                               text=week_rec_promt)
                    await main_bot.send_message(text=ai_rec, chat_id=user.user_id)
                    await users_repository.update_last_rec_week_date_by_user_id(user_id=user.user_id)
                else:
                    continue

            else:
                continue
        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {user.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue


async def send_checkup(main_bot: Bot):
    checkups = await checkup_repository.select_all_active_checkups()
    now_date = datetime.datetime.now()
    for checkup in checkups:
        try:
            if (now_date.time() >= checkup.time_checkup) and ((now_date.date() - checkup.last_date_send.date()) >= datetime.timedelta(days=1)):
                checkup_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
                if checkup_day is None:
                    days_checkup = await days_checkups_repository.get_days_checkups_by_checkup_id(checkup_id=checkup.id)
                    await days_checkups_repository.add_day_checkup(checkup_id=checkup.id,
                                                                   day=len(days_checkup) + 1,
                                                                   points=0)
                    checkup_day = await days_checkups_repository.get_active_day_checkup_by_checkup_id(checkup_id=checkup.id)
                checkup_id, day_checkup_id, type_checkup = checkup.id, checkup_day.id, checkup.type_checkup
                message_photo = checkup_emotions_photo
                check_data = "|".join([str(checkup_id), str(day_checkup_id), type_checkup])
                keyboard = emotions_keyboard(check_data)
                if type_checkup == "productivity":
                    message_photo = checkup_productivity_photo
                    keyboard = productivity_keyboard(check_data)
                await main_bot.send_photo(photo=message_photo,
                                          chat_id=checkup.user_id,
                                          reply_markup=keyboard.as_markup())
                await checkup_repository.update_last_date_send_checkup_by_checkup_id(checkup_id=checkup.id,
                                                                                     last_date_send=now_date)
        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {checkup.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue


async def notification_reminder(main_bot: Bot):
    users = await users_repository.select_all_users()
    now = datetime.datetime.utcnow()  # Можно использовать локальное время, если требуется

    for user in users:
        last_event = await events_repository.get_last_event_by_user_id(user_id=user.user_id)
        if not last_event:
            # Можно реализовать отдельное поведение для новых пользователей без событий
            continue

        delta = now - last_event.creation_date

        # Если не отправлялось уведомление о дневном пороге и прошло >= 1 день
        if not last_event.day_notif_sent and delta >= datetime.timedelta(days=1):
            try:
                await main_bot.send_photo(
                    photo=how_are_you_photo,
                    chat_id=user.user_id,
                    caption="> Добрый день, коллеги\.\.\.\n\n\nВы подготовили отчёт\?📙",
                    parse_mode="MarkdownV2",
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
                    "Уведомление: с момента последнего вашего действия прошла неделя. Рекомендуем вернуться к работе."
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
                    "Уведомление: с момента вашего последнего действия прошел месяц. Мы скучаем и ждем вас снова!"
                )
                last_event.month_notif_sent = True
                await events_repository.update_event(last_event)
            except:
                continue


async def month_checkups(main_bot: Bot):
    users = await users_repository.select_all_users()
    for user in users:
        # print(user.user_id)
        try:
            user_ended_checkups = await checkup_repository.get_ended_checkups_per_month_by_user_id(user_id=user.user_id)
            if user_ended_checkups is not None and len(user_ended_checkups) > 0:
                await main_bot.send_message(chat_id=user.user_id, text="📙Высылаю тебе итоги твоих трекингов за месяц")
                for checkup in user_ended_checkups:
                    try:
                        checkup_days = await days_checkups_repository.get_days_checkups_by_checkup_id(checkup_id=checkup.id)
                        points = [day.points for day in checkup_days]
                        checkup_type = checkup.type_checkup
                        graphic = generate_emotion_chart(emotion_data=points, dates=[day.date_end_day.strftime("%d-%m") for day in checkup_days],
                                                         checkup_type=checkup_type)
                        # graphic = generate_emotion_chart(checkup_type=type_checkup)
                        graphic_bytes = graphic.getvalue()
                        # Отправка голосового сообщения
                        if checkup_type == "emotions":
                            text = f"Cредний показатель твоего эмоционального состояния - {emoji_dict.get(round(sum(points) / len(points)))}"
                        else:
                            text = f"Cредний показатель твоей продуктивности - {speed_dict.get(round(sum(points) / len(points)))}"
                        await main_bot.send_photo(
                            photo=BufferedInputFile(file=graphic_bytes, filename="graphic.png"),
                            chat_id=user.user_id,
                            caption=f"📙Итоговый результат пройденного тобой трекинга.\n\n{text}"
                        )
                        await asyncio.sleep(1)
                    except:
                        print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {user.user_id}\n\n" + traceback.format_exc() + "\n\n")
                        continue

        except:
            print(traceback.format_exc())
            continue


async def update_power_mode_days(main_bot: Bot):
    users = await users_repository.select_all_users()
    now_date = datetime.datetime.now()
    for user in users:
        try:
            user_active_checkups = await checkup_repository.get_active_checkups_by_user_id(user_id=user.user_id)
            if user_active_checkups is not None and len(user_active_checkups) > 0:
                max_date = None
                for checkup in user_active_checkups:
                    last_ended_day = await days_checkups_repository.get_latest_ended_day_checkup_by_checkup_id(checkup_id=checkup.id)
                    if last_ended_day is not None and (max_date is None or last_ended_day.date_end_day > max_date):
                        max_date = last_ended_day.date_end_day
                if max_date is not None and ((now_date - max_date) > datetime.timedelta(hours=24)) and user.power_mode_days != 0:
                    await users_repository.update_power_mode_days_by_user_id(user_id=user.user_id, new_days=0)
                    await main_bot.send_message(chat_id=user.user_id, text="Ох… твои орехи раскололись🌰, но за счёт"
                                                                           " ежедневного трекинга можно начать снова")
        except Exception as e:
            print(f"\n\nВОЗНИКЛА ОШИБКА ОТПРАВКИ ПОЛЬЗОВАТЕЛЮ {user.user_id}\n\n" + traceback.format_exc() + "\n\n")
            continue








