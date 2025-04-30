from typing import Sequence, Optional

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Operations


class OperationRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_operation(self,
                            operation_id: str,
                            user_id: int,
                            is_paid: bool,
                            url: str
                            ) -> bool:
        """

        operation_id = Column(String, nullable=False, primary_key=True)
        is_paid = Column(Boolean, default=False, nullable=False)
        url = Column(String, nullable=False)

        user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
        user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')

        """
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = Operations(user_id=user_id, operation_id=operation_id, is_paid=is_paid, url=url)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    async def get_operation_info_by_id(self, id: int) -> Optional[Operations]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Operations).where(or_(Operations.id == id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_operations(self) -> Sequence[Operations]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Operations)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_operations_by_user_id(self, user_id: int) -> Sequence[Operations]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Operations).where(or_(Operations.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_operation_by_operation_id(self, operation_id: str) -> Optional[Operations]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Operations).where(or_(Operations.operation_id == operation_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def update_paid_by_operation_id(self, operation_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Operations).values({
                    Operations.is_paid: True
                }).where(or_(Operations.operation_id == operation_id))
                await session.execute(sql)
                await session.commit()


