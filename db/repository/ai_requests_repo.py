from datetime import timedelta, datetime, timezone
from typing import Sequence, Optional

from sqlalchemy import select, or_, func, case, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import AiRequests


class AiRequestsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_request(self,
                          answer_ai: str,
                          user_id: int,
                          user_question: str | None = None,
                          has_photo: bool | None = False,
                          has_files: bool | None = False,
                          has_audio: bool | None = False,
                          photo_id: str | None = None,
                          file_id: str | None = None,
                          audio_id: str | None = None,
                          ) -> bool:
        """

            user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
            user: Mapped[Users] = relationship("User", backref=__tablename__, cascade='all', lazy='subquery')
            user_question = Column(String, nullable=False, unique=False)
            answer_ai = Column(String, nullable=True, default="default_answer")
            has_photo = Column(Boolean, nullable=False, default=False)
            photo_id = Column(String, nullable=True)
            has_files = Column(Boolean, nullable=False, default=False)
            file_id = Column(String, nullable=True)
            has_audio = Column(Boolean, nullable=False, default=False)
            audio_id = Column(String, nullable=True)

        """
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = AiRequests(user_id=user_id, answer_ai=answer_ai, photo_id=photo_id, has_photo=has_photo,
                                 has_files=has_files, has_audio=has_audio, audio_id=audio_id, file_id=file_id,
                                 user_question=user_question)
                try:
                    session.add(sql)
                except Exception:
                    return False
                return True

    async def get_request_info_by_id(self, request_id: int) -> Optional[AiRequests]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(AiRequests).where(or_(AiRequests.id == request_id))
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def select_all_requests(self) -> Sequence[AiRequests]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(AiRequests)
                query = await session.execute(sql)
                return query.scalars().all()

    async def select_all_photo_requests(self) -> Sequence[AiRequests]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(AiRequests).where(or_(AiRequests.has_photo == True))
                query = await session.execute(sql)
                return query.scalars().all()

    async def get_requests_by_user_id(self, user_id: int) -> Sequence[AiRequests]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(AiRequests).where(or_(AiRequests.user_id == user_id))
                query = await session.execute(sql)
                return query.scalars().all()

    async def delete_requests_by_user_id(self, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = delete(AiRequests).where(or_(AiRequests.user_id == user_id))
                await session.execute(sql)
                await session.commit()