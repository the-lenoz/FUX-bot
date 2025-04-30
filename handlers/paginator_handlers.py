from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto

from settings import photos_pages
from utils.paginator import MechanicsPaginator

paginator_router = Router()


@paginator_router.callback_query(F.data.startswith("mechanics_paginator"))
async def get_page_paginator(call: CallbackQuery, state: FSMContext):
    call_data = call.data.split(":")
    page_now = int(call_data[2])
    paginator = MechanicsPaginator(page_now)
    if call_data[1] == "page_prev_keys":
        keyboard = paginator.generate_prev_page()
        await call.message.edit_media(media=InputMediaPhoto(media=photos_pages.get(paginator.page_now)),
                                      reply_markup=keyboard)

    elif call_data[1] == "page_next_keys":
        keyboard = paginator.generate_next_page()
        await call.message.edit_media(media=InputMediaPhoto(media=photos_pages.get(paginator.page_now)),
                                      reply_markup=keyboard)
