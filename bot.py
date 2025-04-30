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

from db.engine import DatabaseEngine
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

from settings import storage_bot, token_design_level, redis_host
from utils.activity_middleware import UserActivityMiddleware
from utils.shedulers_bot import edit_activation_sub, send_week_rec, send_checkup, notification_reminder, \
    update_power_mode_days, month_checkups

from utils.user_activity_redis import UserActivityRedis
from utils.user_middleware import EventLoggerMiddleware

main_bot = Bot(token=token_design_level, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def main():
    # redis = await aioredis.from_url(f"redis://{redis_host}", encoding="utf-8", decode_responses=True)
    # activity_tracker = UserActivityRedis(redis=redis)
    db_engine = DatabaseEngine()
    # try:
    await db_engine.proceed_schemas()
    print(await main_bot.get_me())
    await main_bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher(storage=storage_bot)
    dp.update.middleware(EventLoggerMiddleware())
    # dp.update.middleware(UserActivityMiddleware(activity_tracker))
    dp.include_routers(user_router, referral_router, mental_router,
                       payment_router, checkup_router,information_router, system_settings_router, exercises_router,
                       paginator_router, standard_router)
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(func=edit_activation_sub, args=[main_bot], trigger="interval", minutes=60, max_instances=20, misfire_grace_time=120)
    scheduler.add_job(func=send_week_rec, args=[main_bot], trigger="interval", minutes=60, max_instances=20, misfire_grace_time=120)
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
    scheduler.start()
    await dp.start_polling(main_bot, polling_timeout=3)

    # finally:

        # await activity_tracker.close()
        # await main_bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

