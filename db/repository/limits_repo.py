from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from db.engine import DatabaseEngine
from db.models.limits import Limits


class LimitsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def create_user_limits(self, user_id: int, exercises_remaining: int = 2,
                                 universal_requests_remaining: int = 10,
                                 psychological_requests_remaining: int = 30,
                                 attachments_remaining: int = 2,
                                 voices_remaining: int = 2) -> Limits:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                limits = Limits(
                    user_id=user_id,
                    exercises_remaining=exercises_remaining,
                    universal_requests_remaining=universal_requests_remaining,
                    psychological_requests_remaining=psychological_requests_remaining,
                    attachments_remaining=attachments_remaining,
                    voices_remaining=voices_remaining
                )
                session.add(limits)
                await session.commit()
                await session.flush()

                return limits

    async def get_user_limits(self, user_id: int) -> Limits:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Limits).where(or_(Limits.user_id == user_id))
                query = await session.execute(sql)
                result = query.scalars().one_or_none()
                return result if result else await self.create_user_limits(user_id)


    async def update_user_limits(self, user_id: int, exercises_remaining: int = None,
                                 universal_requests_remaining: int = None,
                                 psychological_requests_remaining: int = None,
                                 attachments_remaining: int = None,
                                 voices_remaining: int = None):
        async with self.session_maker() as session:
            session: AsyncSession
            if exercises_remaining is not None\
                    or universal_requests_remaining is not None\
                    or psychological_requests_remaining is not None\
                    or attachments_remaining is not None\
                    or voices_remaining is not None:
                async with session.begin():
                    sql = update(Limits).values({k: v for k, v in {
                        Limits.exercises_remaining: exercises_remaining,
                        Limits.universal_requests_remaining: universal_requests_remaining,
                        Limits.psychological_requests_remaining: psychological_requests_remaining,
                        Limits.attachments_remaining: attachments_remaining,
                        Limits.voices_remaining: voices_remaining
                    }.items() if v is not None}).where(Limits.user_id == user_id)
                    await session.execute(sql)
                    await session.commit()

