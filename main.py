import asyncio
import datetime
import traceback
import types

import aioredis
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bots import admin_bot, main_bot
from db.engine import DatabaseEngine
from handlers.admin_bot_handlers import admin_router
from handlers.checkup_handler import checkup_router
from handlers.exercises_handler import exercises_router
from handlers.information_handler import information_router
from handlers.mental_helper_handler import mental_router
from handlers.paginator_handlers import paginator_router
from handlers.payment_handler import payment_router
from handlers.referral_handler import referral_router
from handlers.standard_handler import standard_router
from handlers.system_settings_handler import system_settings_router
from handlers.user_handler import user_router

from settings import storage_bot, token_design_level, redis_host, token_admin_bot, storage_admin_bot
from utils.activity_middleware import UserActivityMiddleware
from utils.shedulers_bot import edit_activation_sub, send_checkup, notification_reminder, \
    update_power_mode_days, month_checkups, send_weekly_checkups_report

from utils.user_activity_redis import UserActivityRedis
from utils.user_middleware import EventLoggerMiddleware



async def main():
    # redis = await aioredis.from_url(f"redis://{redis_host}", encoding="utf-8", decode_responses=True)
    # activity_tracker = UserActivityRedis(redis=redis)
    db_engine = DatabaseEngine()
    # try:
    await db_engine.proceed_schemas()
    print(await main_bot.get_me())
    await main_bot.delete_webhook(drop_pending_updates=True)
    main_bot_dispatcher = Dispatcher(storage=storage_bot)
    main_bot_dispatcher.update.middleware(EventLoggerMiddleware())
    main_bot_dispatcher.include_routers(user_router, referral_router, mental_router,
                       payment_router, checkup_router,information_router, system_settings_router, exercises_router,
                       paginator_router, standard_router)

    print(await admin_bot.get_me())
    await admin_bot.delete_webhook(drop_pending_updates=True)
    admin_bot_dispatcher = Dispatcher(storage=storage_admin_bot)
    admin_bot_dispatcher.include_routers(admin_router)

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(func=edit_activation_sub, args=[main_bot], trigger="interval", minutes=60, max_instances=20, misfire_grace_time=120)
    scheduler.add_job(func=update_power_mode_days, args=[main_bot], trigger="interval", minutes=30, max_instances=20,
                      misfire_grace_time=120)
    scheduler.add_job(func=send_checkup, args=[main_bot], trigger="interval", minutes=1, max_instances=20,
                      misfire_grace_time=120)
    scheduler.add_job(notification_reminder, trigger='interval', hours=1, args=[main_bot])
    scheduler.add_job(
        month_checkups,
        trigger=CronTrigger(day="last", hour=12, minute=0),
        args=[main_bot],
        id="monthly_checkups_report",
        replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_checkups_report,
        trigger=CronTrigger(day_of_week=6, hour=23, minute=55),
        args=[main_bot],
        id="send_weekly_checkups_report",
        replace_existing=True
    )

    scheduler.start()
    main_bot_task = asyncio.create_task(main_bot_dispatcher.start_polling(main_bot, polling_timeout=3))
    admin_bot_task = asyncio.create_task(admin_bot_dispatcher.start_polling(admin_bot, polling_timeout=3))

    await asyncio.gather(main_bot_task, admin_bot_task)


if __name__ == "__main__":
    asyncio.run(main())

