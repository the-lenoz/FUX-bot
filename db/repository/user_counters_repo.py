from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import update

from db.engine import DatabaseEngine
from db.models.user_counters import UserCounters


class UserCountersRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def create_user_counters(self, user_id: int,
                                    used_exercises: int = 0,
                                    messages_count: int = 0,
                                    dialogs_count: int = 0,
                                    recommendations_count: int = 0,
                                    emotions_tracks_count: int = 0,
                                    productivity_tracks_count: int = 0,
                                    notified_with_recommendation: int = 0,
                                    received_weekly_tracking_reports: int = 0,
                                    received_monthly_tracking_reports: int = 0) -> UserCounters:
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

    async def used_free_recommendation(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.used_free_recommendation: True
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def used_exercises(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.used_exercises: user_counters.used_exercises + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def notified_with_recommendation(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.notified_with_recommendation: user_counters.notified_with_recommendation + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_sent_message(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.messages_count: user_counters.messages_count + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_ended_dialog(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.dialogs_count: user_counters.dialogs_count + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_got_recommendation(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.recommendations_count: user_counters.recommendations_count + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_tracked_emotions(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.emotions_tracks_count: user_counters.emotions_tracks_count + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_tracked_productivity(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.productivity_tracks_count: user_counters.productivity_tracks_count + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_got_weekly_reports(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.received_weekly_tracking_reports: user_counters.received_weekly_tracking_reports + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def user_got_monthly_reports(self, user_id: int):
        user_counters = await self.get_user_counters(user_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(UserCounters).values({
                    UserCounters.received_monthly_tracking_reports: user_counters.received_monthly_tracking_reports + 1
                }).where(or_(UserCounters.user_id == user_id))
                await session.execute(sql)
                await session.commit()
