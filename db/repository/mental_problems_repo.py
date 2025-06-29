from typing import Optional, Sequence

from sqlalchemy import select, and_, or_, update, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import MentalProblem


class MentalProblemsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_problem(self,
                            user_id: int,
                            problem_summary: str) -> int | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                problem = MentalProblem(user_id=user_id, problem_summary=problem_summary)
                try:
                    session.add(problem)
                    await session.commit()
                    await session.flush()
                    return problem.id
                except Exception:
                    return None

    async def get_problem_by_id(self, problem_id: int) -> Optional[MentalProblem]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(MentalProblem).where(or_(MentalProblem.id == problem_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_last_user_problem(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(MentalProblem).where(or_(MentalProblem.user_id == user_id)) \
                    .order_by(desc(MentalProblem.id)).limit(1)
                query = await session.execute(sql)
                return query.scalars().first()

    async def get_all_problems(self) -> Sequence[MentalProblem]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(MentalProblem)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_problems_by_user_id(self, user_id: int, worked_out_threshold: int | None = None) \
            -> Sequence[MentalProblem]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(MentalProblem).where(and_(MentalProblem.user_id == user_id,
                                                       MentalProblem.worked_out < worked_out_threshold
                                                        if worked_out_threshold is not None else True))
                query = await session.execute(sql)
                return query.scalars().all()

    async def worked_out(self, problem_id: int):
        problem = await self.get_problem_by_id(problem_id)
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(MentalProblem).values({
                    MentalProblem.worked_out: problem.worked_out + 1
                }).where(or_(MentalProblem.id == problem_id))
                await session.execute(sql)
                await session.commit()

    async def delete_problems_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(MentalProblem).where(or_(MentalProblem.user_id == user_id))
                await session.execute(sql)
                await session.commit()
