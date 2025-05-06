from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from settings import token_design_level, token_admin_bot

main_bot = Bot(token=token_design_level, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_bot = Bot(token=token_admin_bot, default=DefaultBotProperties(parse_mode=ParseMode.HTML))