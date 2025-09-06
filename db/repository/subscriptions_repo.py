from typing import Sequence

from sqlalchemy import select, or_, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Subscription


class SubscriptionsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_subscription(self, user_id: int, time_limit_subscription: int,
                               active: bool = True, recurrent: bool = False, plan: int = 7):
        """    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
                user: Mapped[Users] = relationship("User", backref=__tablename__, cascade='all', lazy='subquery')
                start_subscription_date = Column(DateTime, nullable=False)
                time_limit_subscription = Column(Integer, nullable=False)
                active = Column(Boolean, nullable=False, default=True)"""
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                user = Subscription(user_id=user_id, time_limit_subscription=time_limit_subscription,
                                    active=active, recurrent=recurrent, plan=plan)
                try:
                    session.add(user)
                    await session.commit()
                except Exception:
                    return False
                return True

    async def get_active_subscription_by_user_id(self, user_id: int) -> Subscription:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscription).where(and_(Subscription.user_id == user_id,
                                                      Subscription.active == True))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_all_subscriptions_by_user_id(self, user_id: int) -> Sequence[Subscription]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscription).where(and_(Subscription.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_subscription_by_id(self, id: int) -> Subscription:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscription).where(or_(Subscription.id == id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_subscriptions(self) -> Sequence[Subscription]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscription)
                query = await session.execute(sql)
                return query.scalars().all()

    async def select_all_active_subscriptions(self) -> Sequence[Subscription]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Subscription).where(or_(Subscription.active == True))
                query = await session.execute(sql)
                return query.scalars().all()

    async def deactivate_subscription(self, subscription_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscription).values({
                    Subscription.active: False
                }).where(or_(Subscription.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def increase_subscription_time_limit(self, subscription_id: int, time_to_add):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscription).values({
                    Subscription.time_limit_subscription: Subscription.time_limit_subscription + time_to_add
                }).where(or_(Subscription.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def update_recurrent(self, subscription_id: int, recurrent: bool = False):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscription).values({
                    Subscription.recurrent: recurrent
                }).where(or_(Subscription.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def update_plan(self, subscription_id: int, new_plan: int = 7):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscription).values({
                    Subscription.plan: new_plan
                }).where(or_(Subscription.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def update_send_notification_subscription(self, subscription_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Subscription).values({
                    Subscription.send_notification: True
                }).where(or_(Subscription.id == subscription_id))
                await session.execute(sql)
                await session.commit()

    async def delete_subscription_by_id(self, id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(Subscription).where(or_(Subscription.id == id))
                await session.execute(sql)
                await session.commit()

    async def get_active_subscriptions_count(self) -> int:
        """
        Возвращает количество активных подписок (active = True).
        """
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                query = select(func.count(Subscription.user_id)).where(or_(Subscription.active == True))
                result = await session.execute(query)
                count_active = result.scalar() or 0
                return count_active

    async def delete_subscriptions_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(Subscription).where(or_(Subscription.user_id == user_id))
                await session.execute(sql)
                await session.commit()
