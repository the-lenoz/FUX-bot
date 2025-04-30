"""
    Функции для работы с базой данных
"""
import asyncio
from typing import Union, Any
from .configuration import DatabaseConfig
from .base import BaseModel
import sqlalchemy.ext.asyncio  # type: ignore
from sqlalchemy import MetaData  # type: ignore
from sqlalchemy.engine import URL  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, \
    create_async_engine as _create_async_engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore


class DatabaseEngine:

    def __create_async_engine(self, url: Union[URL, str]) -> AsyncEngine:
        # echo=True
        return _create_async_engine(url=url, pool_pre_ping=True, echo=False)

    async def __proceed_schemas(self, engine: AsyncEngine, metadata: MetaData) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    def __get_session_maker(self, engine: AsyncEngine) -> sessionmaker:
        return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    def create_session(self):
        async_engine = self.__create_async_engine(DatabaseConfig().build_connection_str())
        return self.__get_session_maker(engine=async_engine)

    async def proceed_schemas(self):
        async_engine = self.__create_async_engine(DatabaseConfig().build_connection_str())
        await self.__proceed_schemas(engine=async_engine, metadata=BaseModel.metadata)
