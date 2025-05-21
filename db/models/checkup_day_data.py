from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .checkup import Checkup


class CheckupDayData(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'days_checkups'

    checkup_id = Column(BigInteger, ForeignKey('checkups.id'), nullable=False)
    checkup: Mapped[Checkup] = relationship("Checkup", backref=__tablename__, cascade='all', lazy='subquery')
    points = Column(BigInteger, nullable=False, default=0)
    day = Column(BigInteger, nullable=False)
    send_checkup = Column(Boolean, nullable=False, default=False)
    date_end_day = Column(DateTime, nullable=True, unique=False)
    user_id = Column(BigInteger, nullable=False)
    checkup_type = Column(String, nullable=False)

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
