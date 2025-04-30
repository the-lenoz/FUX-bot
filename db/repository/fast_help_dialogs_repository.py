from typing import Sequence, Optional

from sqlalchemy import select, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import DatabaseEngine
from db.models import FastHelpDialogs, FastHelp


class FastHelpDialogsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_fast_help_dialog(self,
                            fast_help_id: int,
                            question: str,
                            answer: str | None = None,
                            ) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = FastHelpDialogs(fast_help_id=fast_help_id, question=question, answer=answer)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[FastHelpDialogs]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(FastHelpDialogs).where(or_(FastHelpDialogs.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def get_active_fast_help_dialogs_by_fast_help_id(self, fast_help_id: int) -> FastHelpDialogs:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelpDialogs).where(and_(FastHelpDialogs.fast_help_id == fast_help_id, FastHelpDialogs.answer == None))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_fast_help_dialogs(self) -> Sequence[FastHelpDialogs]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelpDialogs)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_fast_help_dialogs_by_fast_help_id(self, fast_help_id: int) -> Sequence[FastHelpDialogs]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(FastHelpDialogs).where(or_(FastHelpDialogs.fast_help_id == fast_help_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def update_answer_by_fast_help_dialog_id(self, fast_help_dialog_id: int, answer: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(FastHelpDialogs).values({
                    FastHelpDialogs.answer: answer
                }).where(or_(FastHelpDialogs.id == fast_help_dialog_id))
                await session.execute(sql)
                await session.commit()