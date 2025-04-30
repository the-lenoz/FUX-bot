from datetime import time, datetime
from sqlalchemy import Column, BigInteger, String, Boolean, Integer, ForeignKey, Time, Float, DateTime, func

from db.base import BaseModel, CleanModel


class Users(BaseModel, CleanModel):
    """
    Таблица юзеров
    """
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    username = Column(String, nullable=True, unique=False)
    mental_ai_threat_id = Column(String, nullable=True, unique=True)
    standard_ai_threat_id = Column(String, nullable=True, unique=True)
    gender = Column(String, nullable=True, unique=False)
    age = Column(String, nullable=True, unique=False)
    name = Column(String, nullable=True, unique=False)
    ai_temperature = Column(Float, nullable=True, unique=False, default=1)
    active_subscription = Column(Boolean, nullable=False, unique=False, default=False)
    actual_summary_id = Column(BigInteger, nullable=True, unique=False)
    confirm_politic = Column(Boolean, nullable=False, unique=False, default=False)
    full_registration = Column(Boolean, nullable=False, unique=False, default=False)
    activate_promo = Column(Boolean, nullable=False, unique=False, default=False)
    email = Column(String, nullable=True, unique=False)
    last_rec_week_date = Column(DateTime, nullable=False, default=func.now())
    power_mode_days = Column(BigInteger, nullable=True, unique=False, default=0)

    @property
    def stats(self) -> str:
        """
        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__tablename__}:{self.user_id}>"

    def __repr__(self):
        return self.__str__()
