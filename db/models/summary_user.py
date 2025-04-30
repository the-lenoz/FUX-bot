from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .users import Users


class SummaryUser(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'summary_user'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
    summary = Column(String, nullable=False)
    number_summary = Column(BigInteger, nullable=False, unique=False, default=1)

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
