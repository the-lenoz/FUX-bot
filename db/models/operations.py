from sqlalchemy import Column, BigInteger, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .users import Users


class Operations(BaseModel, CleanModel):
    """Таблица операций по оплате"""
    __tablename__ = 'operations'

    operation_id = Column(String, nullable=False, primary_key=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    url = Column(String, nullable=False)

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')

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
