from sqlalchemy import BigInteger, Column, String

from db.base import CleanModel, BaseModel


class PaymentMethod(BaseModel, CleanModel):
    __tablename__ = 'payment_methods'

    user_id = Column(BigInteger, nullable=False)
    payment_method_id = Column(String)