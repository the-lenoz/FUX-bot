from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from aiogram.dispatcher.event.event import EventObserver

from db.repository import events_repository, users_repository


class EventLoggerMiddleware(BaseMiddleware):
    """
    Middleware для логирования всех событий в базу данных
    """

    def __init__(self):
        self.events_repo = events_repository

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        # Определяем тип события и ID пользователя
        user_id = None
        event_type = None
        # Обработка сообщений
        if event.message:
            user_id = event.message.from_user.id
            if event.message.text:
                event_type = f"message_text"
            elif event.message.photo:
                event_type = f"message_photo"
            elif event.message.document:
                event_type = f"message_document"
            elif event.message.voice:
                event_type = f"message_voice"
            else:
                event_type = f"message_other"
        # Обработка callback-запросов
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            event_type = f"callback_query"

        # Другие типы событий
        elif hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
            event_type = f"event_{event.__class__.__name__}"

        # Логируем событие в БД, если определили user_id и event_type
        if user_id and event_type:
            user = await users_repository.get_user_by_user_id(user_id=user_id)
            if user is not None:
                await self.events_repo.add_event(user_id=user_id, event_type=event_type)

        # Продолжаем обработку события
        return await handler(event, data)
