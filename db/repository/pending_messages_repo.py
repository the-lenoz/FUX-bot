from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from db.engine import DatabaseEngine
from db.models.pending_messages import PendingMessages


class PendingMessagesRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def register_user(self, user_id: int) -> PendingMessages:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                pending_message = PendingMessages(
                    user_id=user_id
                )
                session.add(pending_message)
                await session.commit()
                await session.flush()

                return pending_message

    async def get_user_pending_messages(self, user_id: int) -> PendingMessages:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(PendingMessages).where(or_(PendingMessages.user_id == user_id))
                query = await session.execute(sql)
                result = query.scalars().one_or_none()
                return result if result else await self.register_user(user_id)


    async def update_user_pending_messages(self, user_id: int, weekly_tracking_date: datetime = False,
                                           monthly_tracking_date: datetime = False,
                                           recommendation_id: int = False):
        await self.get_user_pending_messages(user_id) # Ensure user record exists
        async with self.session_maker() as session:
            session: AsyncSession
            if weekly_tracking_date is not False\
                    or monthly_tracking_date is not False\
                    or recommendation_id is not False:
                async with session.begin():
                    sql = update(PendingMessages).values({k: v for k, v in {
                        PendingMessages.weekly_tracking_date: weekly_tracking_date,
                        PendingMessages.monthly_tracking_date: monthly_tracking_date,
                        PendingMessages.recommendation_id: recommendation_id
                    }.items() if v is not False}).where(PendingMessages.user_id == user_id)
                    await session.execute(sql)
                    await session.commit()

