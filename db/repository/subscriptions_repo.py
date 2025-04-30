from typing import Sequence

from sqlalchemy import select, or_, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Subscriptions


class SubscriptionsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_subscription(self, user_id: int, time_limit_subscription: int, active: bool = True):
        """    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
                user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
                start_subscription_date = Column(DateTime, nullable=False)
                time_limit_subscription = Column(Integer, nullable=False)
                active = Column(Boolean, nullable=False, default=True)"""
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                user = Subscriptions(user_id=user_id, time_limit_subscription=time_limit_subscription,
                                     active=active)
                try:
                    session.add(user)
                except Exception:
                    return False
                return True

    async def get_active_subscription_by_user_id(self, user_id: int) -> Subscriptions:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscriptions).where(and_(Subscriptions.user_id == user_id,
                                                       Subscriptions.active == True))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_subscription_by_id(self, id: int) -> Subscriptions:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscriptions).where(or_(Subscriptions.id == id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_subscriptions(self) -> Sequence[Subscriptions]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscriptions)
                query = await session.execute(sql)
                return query.scalars().all()

    async def select_all_active_subscriptions(self) -> Sequence[Subscriptions]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscriptions).where(or_(Subscriptions.active == True))
                query = await session.execute(sql)
                return query.scalars().all()

    async def deactivate_subscription(self, subscription_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscriptions).values({
                    Subscriptions.active: False
                }).where(or_(Subscriptions.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def update_time_limit_subscription(self, subscription_id: int, new_time_limit):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscriptions).values({
                    Subscriptions.time_limit_subscription: Subscriptions.time_limit_subscription + new_time_limit
                }).where(or_(Subscriptions.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def update_send_notification_subscription(self, subscription_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscriptions).values({
                    Subscriptions.send_notification: True
                }).where(or_(Subscriptions.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def delete_subscription_by_id(self, id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(Subscriptions).where(or_(Subscriptions.id == id))
                await session.execute(sql)
                await session.commit()



    async def get_active_subscriptions_count(self) -> int:
        """
        Возвращает количество активных подписок (active = True).
        """
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                query = select(func.count(Subscriptions.user_id)).where(or_(Subscriptions.active == True))
                result = await session.execute(query)
                count_active = result.scalar() or 0
                return count_active



