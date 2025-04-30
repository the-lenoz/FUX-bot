from sqlalchemy import Column, String, ForeignKey, BigInteger, Boolean

from db.base import BaseModel, CleanModel


class FastHelpDialogs(BaseModel, CleanModel):
    __tablename__ = 'fast_help_dialogs'

    fast_help_id = Column(BigInteger, ForeignKey('fast_help.id'), nullable=False)
    question = Column(String, nullable=False, unique=False)
    answer = Column(String, nullable=True, unique=False)