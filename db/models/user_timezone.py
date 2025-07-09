from sqlalchemy import Column, BigInteger, Interval

from db.base import BaseModel, CleanModel


class UserTimezone(BaseModel, CleanModel):
    """
    Таблица часовых поясов
    """
    __tablename__ = 'user_timezones'

    user_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    timezone_UTC_delta = Column(Interval, nullable=True, unique=False)
