"""
    Базовые классы базы данных
"""
import datetime

from sqlalchemy import Column, DateTime, func, event, Integer, ForeignKey, String, Boolean  # type: ignore
from sqlalchemy.orm import declarative_base

BaseModel = declarative_base()


class CleanModel:
    """
        Базовая модель в базе данных
    """
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    creation_date = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    upd_date = Column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False,
                        default=lambda: datetime.datetime.now(datetime.timezone.utc))

    @property
    def no_upd_time(self) -> datetime:
        """
        Получить время, которое модель не обновлялась
        :return: timedelta
        """
        return self.upd_date - datetime.datetime.now(datetime.timezone.utc)





