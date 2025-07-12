from typing import Sequence

from sqlalchemy import select, or_, update, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import CheckupDayData


class DaysCheckupRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_day_checkup(self,
                            checkup_id: int,
                            day: int,
                            points: int,
                            user_id: int,
                            checkup_type: str) -> bool:

        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = CheckupDayData(checkup_id=checkup_id, day=day, points=points, user_id=user_id, checkup_type=checkup_type)
                try:
                    session.add(sql)
                    await session.commit()
                except Exception:
                    return False
                return True

    async def select_all_days_checkups(self) -> Sequence[CheckupDayData]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(CheckupDayData)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_days_checkups_by_checkup_id(self, checkup_id: int) -> Sequence[CheckupDayData]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(CheckupDayData).where(or_(CheckupDayData.checkup_id == checkup_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_days_checkups_by_user_id(self, user_id: int) -> Sequence[CheckupDayData]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(CheckupDayData).where(CheckupDayData.user_id == user_id)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_day_checkup_by_day_checkup_id(self, day_checkup_id: int) -> CheckupDayData:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(CheckupDayData).where(or_(CheckupDayData.id == day_checkup_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_active_day_checkup_by_checkup_id(self, checkup_id: int) -> CheckupDayData:

        result = await self.get_active_day_checkups_by_checkup_id(checkup_id)
        return result[0] if result else None

    async def get_active_day_checkups_by_checkup_id(self, checkup_id: int) -> Sequence[CheckupDayData]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(CheckupDayData).where(and_(CheckupDayData.checkup_id == checkup_id, CheckupDayData.send_checkup == False))
                query = await session.execute(sql)
                return query.scalars().all()

    async def update_data_by_day_checkup_id(self, day_checkup_id: int, points: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(CheckupDayData).values({
                    CheckupDayData.send_checkup: True,
                    CheckupDayData.points: points,
                    CheckupDayData.date_end_day: func.now()
                }).where(or_(CheckupDayData.id == day_checkup_id))
                await session.execute(sql)
                await session.commit()

    async def get_latest_ended_day_checkup_by_checkup_id(self, checkup_id: int) -> CheckupDayData | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = (
                    select(CheckupDayData).where(and_(CheckupDayData.checkup_id == checkup_id,
                                                      CheckupDayData.date_end_day.isnot(None))).order_by(CheckupDayData.date_end_day.desc())
                )
                result = await session.execute(sql)
                return result.scalars().first()

    async def get_latest_send_day_checkup_by_checkup_id(self, checkup_id: int) -> CheckupDayData | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = (
                    select(CheckupDayData).where(and_(CheckupDayData.checkup_id == checkup_id,
                                                      CheckupDayData.creation_date.isnot(None))).order_by(CheckupDayData.creation_date.desc())
                )
                result = await session.execute(sql)
                return result.scalars().first()

    async def delete_days_checkups_by_checkup_id(self, checkup_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(CheckupDayData).where(or_(CheckupDayData.checkup_id == checkup_id))
                await session.execute(sql)
                await session.commit()