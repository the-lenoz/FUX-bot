import asyncio

from aiogram import Router, F, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.keyboards import menu_keyboard, information_buro_keyboard
from settings import mechanic_dict, photos_pages
from utils.paginator import MechanicsPaginator

information_router = Router()

@information_router.callback_query(F.data == "all_mechanics", any_state)
async def get_all_mechanics(call: CallbackQuery, state: FSMContext):
    # await call.message.answer("Выбери режим, механику которого ты хочешь посмотреть",
    #                           reply_markup=information_buro_keyboard.as_markup())
    # await call.message.delete()
    paginator = MechanicsPaginator(page_now=1)
    keyboard = paginator.generate_now_page()
    await call.message.edit_media(media=InputMediaPhoto(media=photos_pages.get(paginator.page_now)),
                                  reply_markup=keyboard)


# @information_router.callback_query(F.data.startswith("get_mechanic"), any_state)
# async def get_mechanic(call: CallbackQuery, state: FSMContext):
#     mechanic = call.data.split("|")[1]
#     if mechanic != "mental_helper":
#         text = mechanic_dict.get(mechanic)
#         await call.message.answer(text, reply_markup=menu_keyboard.as_markup())
#         await call.message.delete()
#         return
#     text1 = mechanic_dict.get(mechanic).get("fast_help")
#     text2 = mechanic_dict.get(mechanic).get("go_deeper")
#     await call.message.answer(text1)
#     await asyncio.sleep(0.5)
#     await call.message.answer(text2, reply_markup=menu_keyboard.as_markup())
#     await call.message.delete()
