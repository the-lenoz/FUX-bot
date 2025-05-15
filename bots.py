from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from settings import token_design_level, token_admin_bot, storage_bot, storage_admin_bot

main_bot = Bot(token=token_design_level, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_bot = Bot(token=token_admin_bot, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

main_bot_dispatcher = Dispatcher(storage=storage_bot)
admin_bot_dispatcher = Dispatcher(storage=storage_admin_bot)
