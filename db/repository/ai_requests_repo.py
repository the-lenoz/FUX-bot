from datetime import timedelta, datetime
from typing import Sequence, Optional

from sqlalchemy import select, or_, func, case
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
            user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
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

    async def get_ai_requests_statistics(self) -> dict[str, dict[str, int]]:
        """
        Возвращает статистику по запросам к GPT (AiRequests) за различные периоды:
          - за последний день
          - за последнюю неделю
          - за последний месяц (30 дней, упрощённо)
          - за последний квартал (90 дней, упрощённо)
          - за всё время

        Для каждого периода считаются только запросы без аудио (has_audio=False) и среди них:
          - total        (всего запросов без аудио)
          - with_photo   (из них с фото)
          - with_files   (из них с файлом)
        """
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(weeks=1)
        month_ago = now - timedelta(days=30)  # упрощённый вариант "месяц"
        quarter_ago = now - timedelta(days=90)  # упрощённый вариант "квартал"

        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                # 1) За последний день (без аудио)
                day_query = select(
                    func.count(AiRequests.id).label('total'),
                    func.sum(case((AiRequests.has_photo == True, 1), else_=0)).label('with_photo'),
                    func.sum(case((AiRequests.has_files == True, 1), else_=0)).label('with_files'),
                ).where(
                    AiRequests.creation_date >= day_ago,
                    AiRequests.has_audio == False
                )
                day_result = await session.execute(day_query)
                day_row = day_result.first()  # вернётся кортеж или объект Row

                day_stats = {
                    'total': day_row.total or 0,
                    'with_photo': day_row.with_photo or 0,
                    'with_files': day_row.with_files or 0
                }

                # 2) За последнюю неделю (без аудио)
                week_query = select(
                    func.count(AiRequests.id).label('total'),
                    func.sum(case((AiRequests.has_photo == True, 1), else_=0)).label('with_photo'),
                    func.sum(case((AiRequests.has_files == True, 1), else_=0)).label('with_files'),
                ).where(
                    AiRequests.creation_date >= week_ago,
                    AiRequests.has_audio == False
                )
                week_result = await session.execute(week_query)
                week_row = week_result.first()

                week_stats = {
                    'total': week_row.total or 0,
                    'with_photo': week_row.with_photo or 0,
                    'with_files': week_row.with_files or 0
                }

                # 3) За последний месяц (30 дней, без аудио)
                month_query = select(
                    func.count(AiRequests.id).label('total'),
                    func.sum(case((AiRequests.has_photo == True, 1), else_=0)).label('with_photo'),
                    func.sum(case((AiRequests.has_files == True, 1), else_=0)).label('with_files'),
                ).where(
                    AiRequests.creation_date >= month_ago,
                    AiRequests.has_audio == False
                )
                month_result = await session.execute(month_query)
                month_row = month_result.first()

                month_stats = {
                    'total': month_row.total or 0,
                    'with_photo': month_row.with_photo or 0,
                    'with_files': month_row.with_files or 0
                }

                # 4) За последний квартал (90 дней, без аудио)
                quarter_query = select(
                    func.count(AiRequests.id).label('total'),
                    func.sum(case((AiRequests.has_photo == True, 1), else_=0)).label('with_photo'),
                    func.sum(case((AiRequests.has_files == True, 1), else_=0)).label('with_files'),
                ).where(
                    AiRequests.creation_date >= quarter_ago,
                    AiRequests.has_audio == False
                )
                quarter_result = await session.execute(quarter_query)
                quarter_row = quarter_result.first()

                quarter_stats = {
                    'total': quarter_row.total or 0,
                    'with_photo': quarter_row.with_photo or 0,
                    'with_files': quarter_row.with_files or 0
                }

                # 5) За всё время (без аудио)
                all_time_query = select(
                    func.count(AiRequests.id).label('total'),
                    func.sum(case((AiRequests.has_photo == True, 1), else_=0)).label('with_photo'),
                    func.sum(case((AiRequests.has_files == True, 1), else_=0)).label('with_files'),
                ).where(
                    AiRequests.has_audio == False
                )
                all_time_result = await session.execute(all_time_query)
                all_time_row = all_time_result.first()

                all_time_stats = {
                    'total': all_time_row.total or 0,
                    'with_photo': all_time_row.with_photo or 0,
                    'with_files': all_time_row.with_files or 0
                }

                # Возвращаем итоговый словарь со статистикой
                return {
                    'day': day_stats,
                    'week': week_stats,
                    'month': month_stats,
                    'quarter': quarter_stats,
                    'all_time': all_time_stats
                }


