from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .user import User


class ReferralSystem(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'referral_system'

    bring_user_id = Column(BigInteger, nullable=True, unique=False)

    promo_code = Column(String, nullable=False, primary_key=True, unique=True)

    activations = Column(BigInteger, nullable=True, default=0, unique=False)
    days_sub = Column(BigInteger, nullable=False, default=7, unique=False)
    max_activations = Column(BigInteger, nullable=True, unique=False)
    type_promo = Column(String, nullable=False, unique=False, default="standard")
    active = Column(Boolean, nullable=False, default=True, unique=False)
    value = Column(BigInteger, nullable=False, default=0)

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
