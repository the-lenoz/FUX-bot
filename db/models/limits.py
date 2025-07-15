from sqlalchemy import Column, BigInteger, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .user import User


class Limits(BaseModel, CleanModel):
    __tablename__ = 'limits'

    user_id = Column(BigInteger, primary_key=True, nullable=False)

    exercises_remaining = Column(BigInteger, nullable=False, default=0)
    universal_requests_remaining = Column(BigInteger, nullable=False, default=0)
    psychological_requests_remaining = Column(BigInteger, nullable=False, default=0)
