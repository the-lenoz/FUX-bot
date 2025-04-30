from sqlalchemy import Column, BigInteger, Boolean, ForeignKey
from db.base import BaseModel, CleanModel


class MentalProblems(BaseModel, CleanModel):
    __tablename__ = 'mental_problems'

    summary_id = Column(BigInteger, ForeignKey('summary_user.id'), nullable=False)

    # Колонки для каждой проблемы, по умолчанию False (нет проблемы), unique явно указано как False
    self_esteem = Column(Boolean, default=False, nullable=False, unique=False)       # Самооценка
    emotions = Column(Boolean, default=False, nullable=False, unique=False)          # Эмоции
    relationships = Column(Boolean, default=False, nullable=False, unique=False)     # Отношения (для Дани: с кем угодно, кроме романтических)
    love = Column(Boolean, default=False, nullable=False, unique=False)              # Любовь
    career = Column(Boolean, default=False, nullable=False, unique=False)            # Карьера
    finances = Column(Boolean, default=False, nullable=False, unique=False)          # Финансы
    health = Column(Boolean, default=False, nullable=False, unique=False)            # Здоровье
    self_actualization = Column(Boolean, default=False, nullable=False, unique=False)  # Самореализация
    burnout = Column(Boolean, default=False, nullable=False, unique=False)           # Выгорание
    spirituality = Column(Boolean, default=False, nullable=False, unique=False)      # Духовность (для Дани: смысл жизни и т.д.)
