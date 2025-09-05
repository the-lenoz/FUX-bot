"""
    Базовые классы базы данных
"""
import datetime

from sqlalchemy import Column, DateTime, func, event, Integer, ForeignKey, String, Boolean  # type: ignore
from sqlalchemy.orm import declarative_base

from db.time_provider import get_now_utc_time

BaseModel = declarative_base()


class CleanModel:
    """
        Базовая модель в базе данных
    """
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    creation_date = Column(DateTime, nullable=False, default=get_now_utc_time)
    upd_date = Column(DateTime, onupdate=get_now_utc_time, nullable=False,
                        default=get_now_utc_time)

    @property
    def no_upd_time(self) -> datetime:
        """
        Получить время, которое модель не обновлялась
        :return: timedelta
        """
        return self.upd_date - datetime.datetime.now(datetime.timezone.utc)





