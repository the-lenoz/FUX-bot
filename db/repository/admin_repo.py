from typing import Sequence

from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Admin


class AdminRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_admin(self, admin_id: int, username: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                user = Admin(admin_id=admin_id, username=username)
                try:
                    session.add(user)
                except Exception:
                    return False
                return True

    async def get_admin_by_user_id(self, user_id: int) -> Admin:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Admin).where(or_(Admin.admin_id == user_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_admins(self) -> Sequence[Admin]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Admin)
                query = await session.execute(sql)
                return query.scalars().all()

    async def delete_admin_by_admin_id(self, admin_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(Admin).where(or_(Admin.admin_id == admin_id))
                await session.execute(sql)
                await session.commit()

    # async def delete_attempt_by_user_id(self, user_id: int):
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = update(Admins).values({
    #                 Admins.attempts: Admins.attempts - 1
    #             }).where(or_(Admins.id == user_id))
    #             await session.execute(sql)
    #             await session.commit()
    #
    # async def give_attempts_by_user_id(self, user_id: int, attempts: int):
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = update(Admins).values({
    #                 Admins.attempts: Admins.attempts + attempts
    #             }).where(or_(Admins.id == user_id))
    #             await session.execute(sql)
    #             await session.commit()



    # async def update_user_update_date_by_user_id(self, user_id: int):
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             date_now = datetime.now()
    #             sql = update(Admins).values({
    #                 Admins.upd_date: date_now
    #             }).where(or_(Admins.id == user_id))
    #             await session.execute(sql)
    #             await session.commit()



