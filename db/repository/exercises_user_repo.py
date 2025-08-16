from typing import Sequence

from sqlalchemy import select, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Exercise


class ExercisesUserRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_exercise(self, user_id: int, text: str, problem_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                exercise_obj = Exercise(
                    user_id=user_id,
                    text=text,
                    problem_id=problem_id
                )
                session.add(exercise_obj)
                # Выполнить flush, чтобы id был назначен
                await session.commit()
                await session.flush()

                return exercise_obj

    async def get_exercise_by_exercise_id(self, exercise_id: int) -> Exercise:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Exercise).where(or_(Exercise.id == exercise_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_exercises_by_user_id(self, user_id: int) -> Sequence[Exercise]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Exercise).where(or_(Exercise.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_exercises_by_problem_id(self, problem_id: int) -> Sequence[Exercise]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Exercise).where(or_(Exercise.problem_id == problem_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def delete_exercises_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(Exercise).where(or_(Exercise.user_id == user_id))
                await session.execute(sql)
                await session.commit()