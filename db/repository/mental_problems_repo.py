from datetime import datetime, time
from typing import Sequence

from sqlalchemy import select, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import MentalProblems


class MentalProblemsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_mental_problems(self,
                                  summary_id: int,
                                  self_esteem: bool = False,
                                  emotions: bool = False,
                                  relationships: bool = False,
                                  love: bool = False,
                                  career: bool = False,
                                  finances: bool = False,
                                  health: bool = False,
                                  self_actualization: bool = False,
                                  burnout: bool = False,
                                  spirituality: bool = False):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                mental_problem = MentalProblems(
                    summary_id=summary_id,
                    self_esteem=self_esteem,
                    emotions=emotions,
                    relationships=relationships,
                    love=love,
                    career=career,
                    finances=finances,
                    health=health,
                    self_actualization=self_actualization,
                    burnout=burnout,
                    spirituality=spirituality
                )
                try:
                    session.add(mental_problem)
                except Exception:
                    return False
                return True

    async def get_problems_by_summary_id(self, summary_id: int) -> MentalProblems:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(MentalProblems).where(or_(MentalProblems.summary_id == summary_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()
