from typing import Sequence

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Recommendation


class RecommendationsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_recommendation(self, user_id: int, text: str, problem_id: int | None):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                recommendation_obj = Recommendation(
                    user_id=user_id,
                    text=text,
                    problem_id=problem_id
                )
                session.add(recommendation_obj)
                # Выполнить flush, чтобы id был назначен
                await session.commit()
                await session.flush()

                return recommendation_obj

    async def get_recommendation_by_recommendation_id(self, recommendation_id: int) -> Recommendation:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Recommendation).where(or_(Recommendation.id == recommendation_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_recommendations_by_user_id(self, user_id: int) -> Sequence[Recommendation]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Recommendation).where(or_(Recommendation.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_recommendations_by_problem_id(self, problem_id: int) -> Sequence[Recommendation]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Recommendation).where(or_(Recommendation.problem_id == problem_id))
                query = await session.execute(sql)
                return query.scalars().all()
