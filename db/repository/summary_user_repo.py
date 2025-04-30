from datetime import datetime, time
from typing import Sequence

from sqlalchemy import select, or_, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import MentalProblems, SummaryUser


class SummaryUserRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_summary_user(self,user_id: int, summary: str, number_summary: int | None = None):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                mental_problem = SummaryUser(user_id=user_id, summary=summary, number_summary=number_summary)
                try:
                    session.add(mental_problem)
                except Exception:
                    return False
                return True

    async def select_all_summaries(self) -> Sequence[SummaryUser]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(SummaryUser)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_summaries_by_user_id(self, user_id: int) -> Sequence[SummaryUser]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(SummaryUser).where(or_(SummaryUser.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_summary_by_summary_id(self, summary_id: int) -> SummaryUser:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(SummaryUser).where(or_(SummaryUser.id == summary_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_summary_by_user_id_and_number_summary(self, user_id: int, number_summary: int) -> SummaryUser:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(SummaryUser).where(and_(SummaryUser.user_id == user_id, SummaryUser.number_summary == number_summary))
                query = await session.execute(sql)
                return query.scalars().one_or_none()
