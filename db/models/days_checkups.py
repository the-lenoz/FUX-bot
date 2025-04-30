from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean, Date, DateTime, func
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .checkups import Checkups
from .users import Users


class DaysCheckups(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'days_checkups'

    checkup_id = Column(BigInteger, ForeignKey('checkups.id'), nullable=False)
    checkup: Mapped[Checkups] = relationship("Checkups", backref=__tablename__, cascade='all', lazy='subquery')
    points = Column(BigInteger, nullable=False, default=0)
    day = Column(BigInteger, nullable=False)
    send_checkup = Column(Boolean, nullable=False, default=False)
    date_end_day = Column(DateTime, nullable=True, unique=False)

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
