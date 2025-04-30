import datetime
from typing import Sequence, Optional

from sqlalchemy import select, or_, update, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import DatabaseEngine
from db.models import Checkups, DaysCheckups


class CheckupRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_checkup(self,
                          user_id: int,
                          time_checkup: datetime.time,
                          type_checkup: str,
                          number_checkup: int | None = None) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = Checkups(user_id=user_id, number_checkup=number_checkup, type_checkup=type_checkup, time_checkup=time_checkup)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[Checkups]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(Checkups).where(or_(Checkups.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def select_all_checkups(self) -> Sequence[Checkups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Checkups)
                query = await session.execute(sql)
                return query.scalars().all()

    async def select_all_active_checkups(self) -> Sequence[Checkups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Checkups).where(or_(Checkups.end_checkup == False))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_checkups_by_user_id(self, user_id: int) -> Sequence[Checkups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Checkups).where(or_(Checkups.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_checkup_by_checkup_id(self, checkup_id: int) -> Checkups:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Checkups).where(or_(Checkups.id == checkup_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_active_checkups_by_user_id(self, user_id: int) -> Sequence[Checkups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Checkups).options(selectinload(Checkups.user)).where(and_(Checkups.user_id == user_id, Checkups.end_checkup == False))
                query = await session.execute(sql)
                return query.scalars().all()


    async def get_ended_checkups_per_month_by_user_id(self, user_id: int) -> Sequence[Checkups]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                now_date = datetime.datetime.now()
                sql = select(Checkups).where(and_(Checkups.user_id == user_id, Checkups.end_checkup == True,
                                                  now_date - Checkups.creation_date <= datetime.timedelta(days=31)))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_active_checkup_by_user_id_type_checkup(self, user_id: int, type_checkup) -> Checkups:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Checkups).options(selectinload(Checkups.user)).where(and_(Checkups.user_id == user_id,
                                                                                       Checkups.end_checkup == False,
                                                                                       Checkups.type_checkup == type_checkup))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def update_ending_by_checkup_id(self, checkup_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Checkups).values({
                    Checkups.end_checkup: True
                }).where(or_(Checkups.id == checkup_id))
                await session.execute(sql)
                await session.commit()

    async def update_time_checkup_by_checkup_id(self, checkup_id: int, time_checkup: str | datetime.time):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                if type(time_checkup) == str:
                    time_checkup = datetime.datetime.strptime(time_checkup, '%H:%M')
                sql = update(Checkups).values({
                    Checkups.time_checkup: time_checkup
                }).where(or_(Checkups.id == checkup_id))
                await session.execute(sql)
                await session.commit()

    async def update_last_date_send_checkup_by_checkup_id(self, checkup_id: int, last_date_send: datetime):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Checkups).values({
                    Checkups.last_date_send: last_date_send
                }).where(or_(Checkups.id == checkup_id))
                await session.execute(sql)
                await session.commit()

    async def delete_checkup_by_checkup_id(self, checkup_id: int):
        async with self.session_maker() as session:
            async with session.begin():
                # 1) удаляем дни проверки
                await session.execute(
                    delete(DaysCheckups).where( DaysCheckups.checkup_id == checkup_id)
                )
                # 2) затем саму проверку
                await session.execute(
                    delete(Checkups).where(Checkups.id == checkup_id)
                )