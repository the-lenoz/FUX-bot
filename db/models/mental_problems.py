from sqlalchemy import Column, BigInteger, ForeignKey, String

from db.base import BaseModel, CleanModel


class MentalProblem(BaseModel, CleanModel):
    __tablename__ = 'mental_problems'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)

    problem_summary = Column(String)
    worked_out = Column(BigInteger, nullable=False, default=0)

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
