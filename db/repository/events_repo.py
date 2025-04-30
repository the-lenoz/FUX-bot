from typing import Sequence, Optional

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Events


class EventsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_event(self,
                            user_id: int,
                            event_type: str) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = Events(user_id=user_id, event_type=event_type)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    async def get_event_by_id(self, id: int) -> Optional[Events]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Events).where(or_(Events.id == id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_events(self) -> Sequence[Events]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Events)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_events_by_user_id(self, user_id: int) -> Sequence[Events]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Events).where(or_(Events.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_last_event_by_user_id(self, user_id: int) -> Optional[Events]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Events).where(or_(Events.user_id == user_id)).order_by(Events.creation_date.desc())
                query = await session.execute(sql)
                return query.scalars().first()

    async def update_event(self, event: Events) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                try:
                    await session.merge(event)
                except Exception:
                    return False
        return True
