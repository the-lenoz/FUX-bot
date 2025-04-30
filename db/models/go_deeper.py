from sqlalchemy import Column, String, ForeignKey, BigInteger, Boolean, Integer, Date
from sqlalchemy.orm import Mapped, relationship

from db.base import BaseModel, CleanModel
from db.models.users import Users


class GoDeeper(BaseModel, CleanModel):
    __tablename__ = 'go_deeper'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, unique=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
    end_go_deeper = Column(Boolean, nullable=False, default=False)
    number_go_deeper = Column(BigInteger, nullable=False, default=1)
    recommendation = Column(String, nullable=True, unique=False)
    date_send_rec = Column(Date, nullable=True, unique=False)