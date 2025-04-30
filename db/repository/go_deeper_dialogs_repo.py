from typing import Sequence

from sqlalchemy import select, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import GoDeeperDialogs


class GoDeeperDialogsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_go_deeper_dialog(self,
                            go_deeper_id: int,
                            question: str,
                            answer: str | None = None,
                            ) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = GoDeeperDialogs(go_deeper_id=go_deeper_id, question=question, answer=answer)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    # async def get_promo_info_by_user_id(self, user_id: int) -> Optional[GoDeeperDialogs]:
    #     async with self.session_maker() as session:
    #         session: AsyncSession
    #         async with session.begin():
    #             sql = select(GoDeeperDialogs).where(or_(GoDeeperDialogs.bring_user_id == user_id))
    #             query = await session.execute(sql)
    #             return query.scalars().one_or_none()

    async def get_active_go_deeper_dialogs_by_fast_help_id(self, go_deeper_id: int) -> GoDeeperDialogs:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeperDialogs).where(and_(GoDeeperDialogs.go_deeper_id == go_deeper_id, GoDeeperDialogs.answer == None))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_go_deeper_dialogs(self) -> Sequence[GoDeeperDialogs]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeperDialogs)
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_go_deeper_dialogs_by_fast_help_id(self, go_deeper_id: int) -> Sequence[GoDeeperDialogs]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(GoDeeperDialogs).where(or_(GoDeeperDialogs.go_deeper_id == go_deeper_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def update_answer_by_go_deeper_dialog_id(self, go_deeper_dialog_id: int, answer: str):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(GoDeeperDialogs).values({
                    GoDeeperDialogs.answer: answer
                }).where(or_(GoDeeperDialogs.id == go_deeper_dialog_id))
                await session.execute(sql)
                await session.commit()