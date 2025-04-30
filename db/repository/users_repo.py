from datetime import datetime, time, timedelta
from typing import Sequence

from sqlalchemy import select, or_, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Users


class UserRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_user(self, user_id: int, username: str | None = None,
                       gender: str | None = None, age: str | None = None, name: str | None = None):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                user = Users(user_id=user_id, username=username, gender=gender, age=age, name=name)
                try:
                    session.add(user)
                except Exception:
                    return False
                return True

    # async def update_language_id_by_user_id(self, user_id: int, language: int):
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = update(Users).values({
    #                 Users.language: language
    #             }).where(or_(Users.user_id == user_id))
    #             await session.execute(sql)
    #             await session.commit()


    async def get_user_by_user_id(self, user_id: int) -> Users:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Users).where(or_(Users.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_users(self) -> Sequence[Users]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Users)
                query = await session.execute(sql)
                return query.scalars().all()



    async def update_mental_ai_threat_id_by_user_id(self, user_id: int, thread_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.mental_ai_threat_id: thread_id
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_standard_ai_threat_id_by_user_id(self, user_id: int, thread_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.standard_ai_threat_id: thread_id
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_initials_id_by_user_id(self, user_id: int, first_name: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.name: first_name
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_age_by_user_id(self, user_id: int, age: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.age: age
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_full_reg_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.full_registration: True
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_confirm_politic_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.confirm_politic: True
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_activate_promo_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.activate_promo: True
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_gender_by_user_id(self, user_id: int, gender: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.gender: gender
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_email_by_user_id(self, user_id: int, email: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.email: email
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_ai_temperature_by_user_id(self, user_id: int, ai_temperature: float):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.ai_temperature: ai_temperature
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_last_rec_week_date_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.last_rec_week_date: datetime.now()
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def update_power_mode_days_by_user_id(self, user_id: int, new_days: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Users).values({
                    Users.power_mode_days: new_days
                }).where(or_(Users.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def get_user_creation_statistics(self) -> dict[str, int]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                now = datetime.now()

                day_ago = now - timedelta(days=1)
                week_ago = now - timedelta(weeks=1)
                month_ago = now - timedelta(days=30)  # упрощённый вариант
                quarter_ago = now - timedelta(days=90)  # упрощённый вариант

                # За день
                day_count_sql = select(func.count(Users.user_id)).where(Users.creation_date >= day_ago)
                day_count_result = await session.execute(day_count_sql)
                day_count = day_count_result.scalar() or 0

                # За неделю
                week_count_sql = select(func.count(Users.user_id)).where(Users.creation_date >= week_ago)
                week_count_result = await session.execute(week_count_sql)
                week_count = week_count_result.scalar() or 0

                # За месяц
                month_count_sql = select(func.count(Users.user_id)).where(Users.creation_date >= month_ago)
                month_count_result = await session.execute(month_count_sql)
                month_count = month_count_result.scalar() or 0

                # За квартал
                quarter_count_sql = select(func.count(Users.user_id)).where(Users.creation_date >= quarter_ago)
                quarter_count_result = await session.execute(quarter_count_sql)
                quarter_count = quarter_count_result.scalar() or 0

                all_time_sql = select(func.count(Users.user_id))
                all_time_result = await session.execute(all_time_sql)
                all_time_count = all_time_result.scalar() or 0

                return {
                    'day': day_count,
                    'week': week_count,
                    'month': month_count,
                    'quarter': quarter_count,
                    "all_time": all_time_count,
                }

