from datetime import date
from typing import Sequence

from sqlalchemy import select, or_, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession


from db.engine import DatabaseEngine
from db.models import DaysCheckups


class DaysCheckupRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_day_checkup(self,
                          checkup_id: int,
                          day: int,
                          points: int) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = DaysCheckups(checkup_id=checkup_id, day=day, points=points)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    async def select_all_days_checkups(self) -> Sequence[DaysCheckups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(DaysCheckups)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_days_checkups_by_checkup_id(self, checkup_id: int) -> Sequence[DaysCheckups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(DaysCheckups).where(or_(DaysCheckups.checkup_id == checkup_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_day_checkup_by_day_checkup_id(self, day_checkup_id: int) -> DaysCheckups:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(DaysCheckups).where(or_(DaysCheckups.id == day_checkup_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_active_day_checkup_by_checkup_id(self, checkup_id: int) -> DaysCheckups:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(DaysCheckups).where(and_(DaysCheckups.checkup_id == checkup_id, DaysCheckups.send_checkup == False))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def update_data_by_day_checkup_id(self, day_checkup_id: int, points: int) -> DaysCheckups:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(DaysCheckups).values({
                    DaysCheckups.send_checkup: True,
                    DaysCheckups.points: points,
                    DaysCheckups.date_end_day: func.now()
                }).where(or_(DaysCheckups.id == day_checkup_id))
                await session.execute(sql)
                await session.commit()

    async def get_latest_ended_day_checkup_by_checkup_id(self, checkup_id: int) -> DaysCheckups | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = (
                    select(DaysCheckups).where(and_(DaysCheckups.checkup_id == checkup_id,
                                                    DaysCheckups.date_end_day.isnot(None))).order_by(DaysCheckups.date_end_day.desc())
                )
                result = await session.execute(sql)
                return result.scalars().first()
