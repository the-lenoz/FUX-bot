from typing import Sequence

from sqlalchemy import select, or_
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
