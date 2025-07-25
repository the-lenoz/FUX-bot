from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from db.engine import DatabaseEngine
from db.models.user_counters import UserCounters


class UserCountersRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def create_user_counters(self, user_id: int,
                                    used_exercises: int,
                                    messages_count: int,
                                    dialogs_count: int,
                                    recommendations_count: int,
                                    emotions_tracks_count: int,
                                    productivity_tracks_count: int,
                                    notified_with_recommendation: int,
                                    received_weekly_tracking_reports: int,
                                    received_monthly_tracking_reports: int) -> UserCounters:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                limits = UserCounters(
                    user_id=user_id,
                    used_exercises=used_exercises,
                    messages_count=messages_count,
                    dialogs_count=dialogs_count,
                    recommendations_count=recommendations_count,
                    emotions_tracks_count=emotions_tracks_count,
                    productivity_tracks_count=productivity_tracks_count,
                    notified_with_recommendation=notified_with_recommendation,
                    received_weekly_tracking_reports=received_weekly_tracking_reports,
                    received_monthly_tracking_reports=received_monthly_tracking_reports
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



