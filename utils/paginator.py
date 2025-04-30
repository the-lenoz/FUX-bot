import math
from typing import List, Sequence

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



class Paginator:
    def __init__(self, name_of_paginator: str = None,
                 page_now=0):
        self.page_now = page_now
        self.name_paginator = name_of_paginator

    def _generate_page(self):
        ...

    def __str__(self):
        ...


class MechanicsPaginator(Paginator):
    def __init__(self, page_now=1):
        super().__init__(page_now=page_now,
                         name_of_paginator='mechanics_paginator')

    def _generate_page(self) -> InlineKeyboardMarkup:
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 8

        if self.page_now > 8:
            self.page_now = 1

        page_kb.row(InlineKeyboardButton(text='◀️ Назад',
                                         callback_data=f'{self.name_paginator}:page_prev_keys:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{8}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text='Вперед ▶️',
                                         callback_data=f'{self.name_paginator}:page_next_keys:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='🔽 Перейти в стартовое меню',
                                         callback_data='start_menu'))

        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()


