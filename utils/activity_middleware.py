from aiogram import BaseMiddleware
from aiogram.types import Update
from datetime import datetime

from utils.user_activity_redis import UserActivityRedis


class UserActivityMiddleware(BaseMiddleware):
    def __init__(self, tracker: UserActivityRedis):
        self.tracker = tracker
        super().__init__()

    async def __call__(self, handler, event, data):
        user_id = None
        activity = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
                activity = "send_message"
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
                activity = "callback_query"
        if user_id:
            await self.tracker.log_user_activity(user_id=user_id, activity=activity)
        return await handler(event, data)

