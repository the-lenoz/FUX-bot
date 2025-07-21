from sqlalchemy import Column, BigInteger

from db.base import BaseModel, CleanModel


class UserCounters(BaseModel, CleanModel):
    __tablename__ = 'user_counters'

    user_id = Column(BigInteger, primary_key=True, nullable=False)

    used_exercises = Column(BigInteger, nullable=False, default=0)
    messages_count = Column(BigInteger, nullable=False, default=0)
    recommendations_count = Column(BigInteger, nullable=False, default=0)
    emotions_tracks_count = Column(BigInteger, nullable=False, default=0)
    productivity_tracks_count = Column(BigInteger, nullable=False, default=0)
    notified_with_recommendation = Column(BigInteger, nullable=False, default=0)
    received_weekly_tracking_reports = Column(BigInteger, nullable=False, default=0)
    received_monthly_tracking_reports = Column(BigInteger, nullable=False, default=0)