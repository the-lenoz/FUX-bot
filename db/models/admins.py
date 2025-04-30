from sqlalchemy import Column, BigInteger, String

from db.base import BaseModel, CleanModel


class Admins(BaseModel, CleanModel):
    """
    Таблица юзеров
    """
    __tablename__ = 'admins'

    admin_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    username = Column(String, nullable=True, unique=False)

    @property
    def stats(self) -> str:
        """
        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__tablename__}:{self.admin_id}>"

    def __repr__(self):
        return self.__str__()
