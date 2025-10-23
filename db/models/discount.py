from sqlalchemy import Column, BigInteger, DateTime

from db.base import CleanModel, BaseModel


class Discount(CleanModel, BaseModel):
    __tablename__ = "discounts"

    user_id = Column(BigInteger, nullable=False)
    end_timestamp = Column(DateTime, nullable=False)
    value = Column(BigInteger, nullable=False) # in percents