from sqlalchemy import Column, String, ForeignKey, BigInteger, Boolean

from db.base import BaseModel, CleanModel


class GoDeeperDialogs(BaseModel, CleanModel):
    __tablename__ = 'go_deeper_dialogs'

    go_deeper_id = Column(BigInteger, ForeignKey('go_deeper.id'), nullable=False)
    question = Column(String, nullable=False, unique=False)
    answer = Column(String, nullable=True, unique=False)