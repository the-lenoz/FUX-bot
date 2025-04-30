from datetime import datetime, time
from typing import Sequence

from sqlalchemy import select, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import ExercisesUser


class ExercisesUserRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_exercise(self, user_id: int, exercise: str, answer: str | None = None, feedback: str | None = None):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                exercise_obj = ExercisesUser(
                    user_id=user_id,
                    exercise=exercise,
                    user_answer=answer,
                    feedback=feedback
                )
                try:
                    session.add(exercise_obj)
                    # Выполнить flush, чтобы id был назначен
                    await session.flush()
                except Exception:
                    return False
                return exercise_obj

    async def get_exercise_by_exercise_id(self, exercise_id: int) -> ExercisesUser:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(ExercisesUser).where(or_(ExercisesUser.id == exercise_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_exercises_by_user_id(self, user_id: int) -> Sequence[ExercisesUser]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(ExercisesUser).where(or_(ExercisesUser.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def update_answer_by_exercise_id(self, exercise_id: int, user_answer: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(ExercisesUser).values({
                    ExercisesUser.user_answer: user_answer
                }).where(or_(ExercisesUser.id == exercise_id))
                await session.execute(sql)
                await session.commit()

    async def update_feedback_by_exercise_id(self, exercise_id: int, feedback: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(ExercisesUser).values({
                    ExercisesUser.feedback: feedback
                }).where(or_(ExercisesUser.id == exercise_id))
                await session.execute(sql)
                await session.commit()
