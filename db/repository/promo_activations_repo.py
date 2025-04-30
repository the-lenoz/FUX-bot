from typing import Sequence, Optional

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import PromoActivations


class PromoActivationsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_activation(self,
                          promo_id: int,
                          activate_user_id: int,
                          ) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = PromoActivations(promo_id=promo_id, activate_user_id=activate_user_id)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[PromoActivations]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(PromoActivations).where(or_(PromoActivations.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def select_all_activations(self) -> Sequence[PromoActivations]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(PromoActivations)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_activations_by_promo_id(self, promo_id: int) -> Sequence[PromoActivations]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(PromoActivations).where(or_(PromoActivations.promo_id == promo_id))
                query = await session.execute(sql)
                return query.scalars().all()

    # async def update_activation_by_promo_id(self, promo_id: int):
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = update(PromoActivations).values({
    #                 PromoActivations.activated: True,
    #             }).where(or_(PromoActivations.id == promo_id))
    #             await session.execute(sql)
    #             await session.commit()


