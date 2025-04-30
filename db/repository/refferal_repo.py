from typing import Sequence, Optional

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import ReferralSystem


class ReferralSystemRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_promo(self,
                          promo_code: str,
                          max_days: int | None = None,
                          max_activations: int | None = None,
                          bring_user_id: int | None = None,
                          type_promo: str | None = None,
                          ) -> bool:
        """

    bring_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, unique=True)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
    activate_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True, default=None, unique=True)
    promo_code = Column(String, nullable=False, primary_key=True, unique=True)
    activated = Column(Boolean, nullable=False, default=False)

        """
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = ReferralSystem(bring_user_id=bring_user_id, promo_code=promo_code,
                                     days_sub=max_days, max_activations=max_activations,
                                     type_promo=type_promo)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[ReferralSystem]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(ReferralSystem).where(or_(ReferralSystem.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def select_all_promo(self) -> Sequence[ReferralSystem]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(ReferralSystem)
                query = await session.execute(sql)
                return query.scalars().all()

    async def select_all_promo_codes(self) -> set:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(ReferralSystem.promo_code)
                query = await session.execute(sql)
                return set(query.scalars().all())

    async def get_promo_by_bring_user_id(self, bring_user_id: int) -> ReferralSystem:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(ReferralSystem).where(or_(ReferralSystem.bring_user_id == bring_user_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def get_promo_by_promo_code(self, promo_code: str) -> ReferralSystem:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(ReferralSystem).where(or_(ReferralSystem.promo_code == promo_code))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def update_activations_by_promo_id(self, promo_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(ReferralSystem).values({
                    ReferralSystem.activations: ReferralSystem.activations + 1,
                }).where(or_(ReferralSystem.id == promo_id))
                await session.execute(sql)
                await session.commit()


