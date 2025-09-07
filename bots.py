from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from data.secrets import main_bot_token, admin_bot_token

storage_bot = MemoryStorage()
storage_admin_bot = MemoryStorage()

main_bot = Bot(token=main_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_bot = Bot(token=admin_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

main_bot_dispatcher = Dispatcher(storage=storage_bot)
admin_bot_dispatcher = Dispatcher(storage=storage_admin_bot)
