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
        page_kb.row(InlineKeyboardButton(text='🔽 Готов(а) Начать',
                                         callback_data='start_use'))

        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()


def create_paginated_keyboard(items: dict[str, int],
                              callback_data_format: str,
                              page_callback_data_format: str,
                              cancel_callback_data: str | None = None,
                              page: int = 0) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с разбивкой на страницы.

    :param page_callback_data_format: Строка для форматирования callback_data paginator'a.
    :param items: Словарь с элементами вида {name: id}.
    :param callback_data_format: Строка для форматирования callback_data.
    :param cancel_callback_data:
    :param page: Текущая страница.
    :return: Объект InlineKeyboardMarkup.
    """

    builder = InlineKeyboardBuilder()
    items_per_page = 12
    item_list = list(items.items())
    start_index = page * items_per_page
    end_index = start_index + items_per_page

    # Добавляем кнопки для текущей страницы
    for name, item_id in item_list[start_index:end_index]:
        builder.row(InlineKeyboardButton(text=name, callback_data=callback_data_format.format(item_id)))

    navigation_buttons = []
    # Добавляем кнопку "Назад", если это не первая страница
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=page_callback_data_format.format(page - 1)))

    # Добавляем кнопку "Вперед", если есть еще элементы
    if end_index < len(item_list):
        navigation_buttons.append(InlineKeyboardButton(text="▶️ Вперед", callback_data=page_callback_data_format.format(page + 1)))

    if navigation_buttons:
        builder.row(*navigation_buttons)
    if cancel_callback_data:
        builder.row(InlineKeyboardButton(text="Отмена", callback_data=cancel_callback_data))

    return builder.as_markup()