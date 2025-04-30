from datetime import datetime, timedelta

from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean, Time, DateTime, func
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .users import Users


class Checkups(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'checkups'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, unique=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
    end_checkup = Column(Boolean, nullable=False, default=False)
    number_checkup = Column(BigInteger, nullable=False)
    type_checkup = Column(String, nullable=False)
    time_checkup = Column(Time, nullable=True, unique=False)
    last_date_send = Column(DateTime, nullable=True, unique=False, default=func.now() - timedelta(days=1))

    @property
    def stats(self) -> str:
        """
       :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__tablename__}:{self.id}>"

    def __repr__(self):
        return self.__str__()
