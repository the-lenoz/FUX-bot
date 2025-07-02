import asyncio
import logging
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bots import admin_bot, main_bot, main_bot_dispatcher, admin_bot_dispatcher
from db.engine import DatabaseEngine
from handlers.admin_bot_handlers import admin_router
from handlers.checkup_handler import checkup_router
from handlers.exercises_handler import exercises_router
from handlers.information_handler import information_router
from handlers.paginator_handlers import paginator_router
from handlers.payment_handler import payment_router
from handlers.referral_handler import referral_router
from handlers.standard_handler import standard_router
from handlers.sub_management_handler import sub_management_router
from handlers.system_settings_handler import system_settings_router
from handlers.user_handler import user_router
from utils.shedulers_bot import edit_activation_sub, send_checkup, notification_reminder, \
    break_power_mode, send_recommendations, send_user_statistics
from utils.user_middleware import EventLoggerMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler(f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    db_engine = DatabaseEngine()
    await db_engine.proceed_schemas()
    print(await main_bot.get_me())
    await main_bot.delete_webhook(drop_pending_updates=True)

    main_bot_dispatcher.update.middleware(EventLoggerMiddleware())
    main_bot_dispatcher.include_routers(sub_management_router, user_router, referral_router,
                       payment_router, checkup_router,information_router, system_settings_router, exercises_router,
                       paginator_router, standard_router)

    print(await admin_bot.get_me())
    await admin_bot.delete_webhook(drop_pending_updates=True)

    admin_bot_dispatcher.include_routers(admin_router)

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(func=edit_activation_sub, args=[main_bot], trigger="interval",
                      minutes=60, max_instances=20, misfire_grace_time=120)
    scheduler.add_job(func=break_power_mode, args=[main_bot], trigger="interval", minutes=30, max_instances=20,
                      misfire_grace_time=120)
    scheduler.add_job(func=send_checkup, trigger="interval", minutes=1, max_instances=20,
                      misfire_grace_time=120)
    scheduler.add_job(func=send_recommendations, args=[main_bot], trigger="interval",
                      minutes=10, max_instances=20, misfire_grace_time=120)
    scheduler.add_job(notification_reminder, trigger='interval', hours=1, args=[main_bot])
    scheduler.add_job(
        send_user_statistics,
        trigger=CronTrigger(hour=22),
        args=[admin_bot]
    )

    scheduler.start()
    main_bot_task = asyncio.create_task(main_bot_dispatcher.start_polling(main_bot, polling_timeout=3))
    admin_bot_task = asyncio.create_task(admin_bot_dispatcher.start_polling(admin_bot, polling_timeout=3))

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(stop(loop, signal.SIGTERM)))
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(stop(loop, signal.SIGINT)))
    await asyncio.gather(main_bot_task, admin_bot_task)


async def stop(loop, sig):
    logger.info(f"Received signal {sig.name if sig else 'None'}, shutting down gracefully...")

    # Остановить поллинг диспетчера
    await main_bot_dispatcher.stop_polling()
    await admin_bot_dispatcher.stop_polling()

    # Выполнить очистку ресурсов, если необходимо
    await main_bot.close()
    await admin_bot.close()

    # Остановить цикл событий asyncio
    loop.stop()
    logger.info("Event loop stopped.")


if __name__ == "__main__":
    asyncio.run(main())

