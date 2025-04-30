from sqlalchemy import Column, BigInteger, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .users import Users


class AiRequests(BaseModel, CleanModel):
    """Таблица запросов к gpt"""
    __tablename__ = 'ai_requests'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')
    user_question = Column(String, nullable=False, unique=False)
    answer_ai = Column(String, nullable=True, default="default_answer")
    has_photo = Column(Boolean, nullable=False, default=False)
    photo_id = Column(String, nullable=True)
    has_files = Column(Boolean, nullable=False, default=False)
    file_id = Column(String, nullable=True)
    has_audio = Column(Boolean, nullable=False, default=False)
    audio_id = Column(String, nullable=True)

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
