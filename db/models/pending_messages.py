from sqlalchemy import Column, BigInteger, DateTime

from db.base import BaseModel, CleanModel


class PendingMessages(BaseModel, CleanModel):
    __tablename__ = 'pending_messages'

    user_id = Column(BigInteger, primary_key=True, nullable=False)

    weekly_tracking_date = Column(DateTime, default=None)
    monthly_tracking_date = Column(DateTime, default=None)
    recommendation_id = Column(BigInteger, default=None)
