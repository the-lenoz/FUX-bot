from datetime import datetime
from typing import Sequence

from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Discount


class DiscountRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def create_discount(self, user_id: int, end_timestamp: datetime, value: int) -> Discount:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                discount = Discount(
                    user_id=user_id,
                    end_timestamp=end_timestamp,
                    value=value
                )
                session.add(discount)
                await session.commit()
                await session.flush()

                return discount

    async def get_discount_by_id(self, discount_id: int) -> Discount:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Discount).where(or_(Discount.id == discount_id))
                query = await session.execute(sql)
                result = query.scalars().one_or_none()
                return result

    async def get_discounts_by_user_id(self, user_id: int) -> Sequence[Discount]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Discount).where(or_(Discount.user_id == user_id))
                query = await session.execute(sql)
                result = query.scalars().all()
                return result

    async def delete_discount_by_id(self, discount_id: int) -> None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(Discount).where(or_(Discount.discount_id == discount_id))
                await session.execute(sql)
                await session.commit()