from sqlalchemy import Column, BigInteger, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .user import User


class Recommendation(BaseModel, CleanModel):
    __tablename__ = 'recommendations'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    problem_id = Column(BigInteger, ForeignKey('mental_problems.id'), nullable=False)

    text = Column(String)



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
