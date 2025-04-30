import aioredis
from typing import List

class UserActivityRedis:
    def __init__(self, redis: aioredis.Redis):
        """
        Инициализация с объектом подключения к Redis.
        """
        self.redis = redis
        # Ключ для хранения множества зарегистрированных пользователей
        self.registered_users_key = "registered_users"
        # Префикс для ключей с данными активности, например: "activity:<user_id>"
        self.activity_prefix = "activity:"

    # Методы для работы с зарегистрированными пользователями
    async def get_registered_users(self) -> List[int]:
        """
        Возвращает список зарегистрированных user_id из Redis.
        """
        members = await self.redis.smembers(self.registered_users_key)
        # Предполагаем, что user_id хранятся как строки, преобразуем в int.
        return [int(member) for member in members]

    async def add_registered_user(self, user_id: int) -> None:
        """
        Добавляет одного пользователя в множество зарегистрированных пользователей.
        """
        await self.redis.sadd(self.registered_users_key, user_id)

    async def set_registered_users(self, user_ids: List[int]) -> None:
        """
        Перезаписывает множество зарегистрированных пользователей переданным списком.
        """
        # Удаляем старое множество
        await self.redis.delete(self.registered_users_key)
        if user_ids:
            # Добавляем сразу несколько user_id; redis-py/aioredis поддерживают передачу переменного числа аргументов
            await self.redis.sadd(self.registered_users_key, *user_ids)

    # Методы для работы с активностью пользователей
    async def log_user_activity(self, user_id: int, activity: str) -> None:
        """
        Добавляет запись об активности для указанного пользователя.
        Например, запись может выглядеть как: "2025-03-14T12:00:00 - sent_message".
        """
        key = f"{self.activity_prefix}{user_id}"
        await self.redis.rpush(key, activity)
        # Устанавливаем TTL для данных активности (например, 3600 секунд)
        await self.redis.expire(key, 3600)

    async def get_user_activity(self, user_id: int) -> List[str]:
        """
        Возвращает список записей активности для указанного пользователя.
        """
        key = f"{self.activity_prefix}{user_id}"
        return await self.redis.lrange(key, 0, -1)

    async def close(self) -> None:
        """
        Закрывает соединение с Redis.
        """
        await self.redis.close()
