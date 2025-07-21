from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from db.engine import DatabaseEngine
from db.models.user_counters import UserCounters


class UserCountersRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def create_user_counters(self, user_id: int, exercises_remaining: int = 2,
                                 universal_requests_remaining: int = 10,
                                 psychological_requests_remaining: int = 30) -> UserCounters:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                limits = UserCounters(
                    user_id=user_id,
                    exercises_remaining=exercises_remaining,
                    universal_requests_remaining=universal_requests_remaining,
                    psychological_requests_remaining=psychological_requests_remaining
                )
                session.add(limits)
                await session.commit()
                await session.flush()

                return limits

    async def get_user_counters(self, user_id: int) -> UserCounters:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(UserCounters).where(or_(UserCounters.user_id == user_id))
                query = await session.execute(sql)
                result = query.scalars().one_or_none()
                return result if result else await self.create_user_counters(user_id)



