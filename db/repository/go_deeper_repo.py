from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import select, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import DatabaseEngine
from db.models import GoDeeper


class GoDeeperRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_go_deeper(self,
                          user_id: int,
                          number_go_deeper: int | None = None,
                          ) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = GoDeeper(user_id=user_id, number_go_deeper=number_go_deeper)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[GoDeeper]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(GoDeeper).where(or_(GoDeeper.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def select_all_fgo_deepers(self) -> Sequence[GoDeeper]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeper)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_go_deepers_by_user_id(self, user_id: int) -> Sequence[GoDeeper]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeper).where(or_(GoDeeper.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_go_deeper_by_go_deeper_id(self, go_deeper_id: int) -> GoDeeper:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeper).where(or_(GoDeeper.id == go_deeper_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_active_go_deeper_by_user_id(self, user_id: int) -> GoDeeper:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeper).options(selectinload(GoDeeper.user)).where(and_(GoDeeper.user_id == user_id, GoDeeper.end_go_deeper == False))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def update_ending_by_go_deeper_id(self, go_deeper_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(GoDeeper).values({
                    GoDeeper.end_go_deeper: True
                }).where(or_(GoDeeper.id == go_deeper_id))
                await session.execute(sql)
                await session.commit()

    async def update_recommendation_by_go_deeper_id(self, go_deeper_id: int, recommendation: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(GoDeeper).values({
                    GoDeeper.end_go_deeper: True,
                    GoDeeper.recommendation: recommendation
                }).where(or_(GoDeeper.id == go_deeper_id))
                await session.execute(sql)
                await session.commit()

    async def get_ended_go_deeper_by_user_id(self, user_id: int) -> Sequence[GoDeeper]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeper).where(and_(GoDeeper.user_id == user_id, GoDeeper.end_go_deeper == True))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_user_go_deepers_by_user_id_and_period(self, user_id: int, period_days = int) -> Sequence[GoDeeper]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeper).where(and_(GoDeeper.user_id == user_id, (datetime.now() - GoDeeper.creation_date) <= timedelta(days=float(period_days))))
                query = await session.execute(sql)
                return query.scalars().all()