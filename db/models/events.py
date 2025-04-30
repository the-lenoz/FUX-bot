from sqlalchemy import Column, String, ForeignKey, BigInteger, Boolean

from db.base import BaseModel, CleanModel


class Events(BaseModel, CleanModel):
    __tablename__ = 'events'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    event_type = Column(String, nullable=False)

    day_notif_sent = Column(Boolean, default=False, nullable=False)
    week_notif_sent = Column(Boolean, default=False, nullable=False)
    month_notif_sent = Column(Boolean, default=False, nullable=False)

    @property
    def stats(self) -> str:
        """
        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__tablename__}:{self.user_id}>"

    def __repr__(self):
        return self.__str__()