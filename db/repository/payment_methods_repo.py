from sqlalchemy import select, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models.payment_methods import PaymentMethod


class PaymentMethodsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_payment_method(self, user_id: int, payment_method_id: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                payment_method_obj = PaymentMethod(
                    user_id=user_id,
                    payment_method_id=payment_method_id
                )
                session.add(payment_method_obj)
                # Выполнить commit, чтобы id был назначен
                await session.commit()

                return payment_method_obj

    async def get_payment_method_by_user_id(self, user_id: int) -> PaymentMethod:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(PaymentMethod).where(or_(PaymentMethod.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def update_payment_method_by_user_id(self, user_id: int, payment_method_id: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(PaymentMethod).values(payment_method_id=payment_method_id)\
                    .where(or_(PaymentMethod.user_id == user_id))
                await session.execute(sql)
                await session.commit()

    async def delete_payment_method_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(PaymentMethod).where(or_(PaymentMethod.user_id == user_id))
                await session.execute(sql)
                await session.commit()