from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .users import Users


class ReferralSystem(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'referral_system'

    bring_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True, unique=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
    # activate_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True, default=None, unique=True)
    promo_code = Column(String, nullable=False, primary_key=True, unique=True)
    # activated = Column(Boolean, nullable=False, default=False)
    activations = Column(BigInteger, nullable=True, default=0, unique=False)
    days_sub = Column(BigInteger, nullable=False, default=7, unique=False)
    max_activations = Column(BigInteger, nullable=True, unique=False)
    type_promo = Column(String, nullable=False, unique=False, default="standard")
    active = Column(Boolean, nullable=False, default=True, unique=False)

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
