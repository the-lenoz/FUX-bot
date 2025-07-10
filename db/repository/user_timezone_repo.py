from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models.user_timezone import UserTimezone


class UserTimezoneRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def set_user_timezone_delta(self, user_id: int, timezone_utc_delta: timedelta):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                query = insert(UserTimezone).values(user_id=user_id,
                    timezone_UTC_delta=timezone_utc_delta).on_conflict_do_update(index_elements=[UserTimezone.user_id],
                                                                                 set_=dict(timezone_UTC_delta=timezone_utc_delta))

                await session.execute(query)
                await session.commit()

    async def get_user_timezone_delta(self, user_id: int) -> timedelta | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                query = select(UserTimezone).where(UserTimezone.user_id == user_id)
                result = await session.execute(query)
                timezone: UserTimezone = result.scalars().one_or_none()
                if timezone:
                    return timezone.timezone_UTC_delta
                return None