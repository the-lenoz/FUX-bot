from datetime import datetime, timedelta
from typing import Sequence, Optional

from sqlalchemy import select, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import DatabaseEngine
from db.models import FastHelp


class FastHelpRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_fast_help(self,
                          user_id: int,
                          number_fast_help: int | None = None,
                          ) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = FastHelp(user_id=user_id, number_fast_help=number_fast_help)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[FastHelp]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(FastHelp).where(or_(FastHelp.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def select_all_fast_helps(self) -> Sequence[FastHelp]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelp)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_fast_helps_by_user_id(self, user_id: int) -> Sequence[FastHelp]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelp).where(or_(FastHelp.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_fast_help_by_fast_help_id(self, fast_help_id: int) -> FastHelp:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelp).where(or_(FastHelp.id == fast_help_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_active_fast_help_by_user_id(self, user_id: int) -> FastHelp:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelp).options(selectinload(FastHelp.user)).where(and_(FastHelp.user_id == user_id, FastHelp.end_fast_help == False))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_ended_fast_help_by_user_id(self, user_id: int) -> Sequence[FastHelp]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelp).options(selectinload(FastHelp.user)).where(and_(FastHelp.user_id == user_id, FastHelp.end_fast_help == True))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_user_fast_helps_by_user_id_and_period(self, user_id: int, period_days = int) -> Sequence[FastHelp]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelp).where(and_(FastHelp.user_id == user_id, (datetime.now() - FastHelp.creation_date) <= timedelta(days=float(period_days))))
                query = await session.execute(sql)
                return query.scalars().all()

    async def update_ending_by_fast_help_id(self, fast_help_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(FastHelp).values({
                    FastHelp.end_fast_help: True
                }).where(or_(FastHelp.id == fast_help_id))
                await session.execute(sql)
                await session.commit()

    async def update_recommendation_by_fast_help_id(self, fast_help_id: int, recommendation: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(FastHelp).values({
                    FastHelp.recommendation: recommendation
                }).where(or_(FastHelp.id == fast_help_id))
                await session.execute(sql)
                await session.commit()