from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .users import Users


class PromoActivations(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'promo_activations'

    promo_id = Column(BigInteger, ForeignKey('referral_system.id'), primary_key=True, unique=False)
    activate_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, unique=False)

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
