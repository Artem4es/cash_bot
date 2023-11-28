from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, declarative_base, sessionmaker
from src.config import settings


async_engine = create_async_engine(url=settings.DATABASE_URL_asyncpg, echo=True)
sync_engine = create_engine(url=settings.DATABASE_URL_sync, echo=True)

async_session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
sync_session_maker = sessionmaker(sync_engine, expire_on_commit=False)
class Base(DeclarativeBase):
    pass


# async def get_async_session() -> AsyncGenerator:   # тут вряд ли понадобится...
#     async with async_sessionmaker(bind=async_engine) as session:
#         yield session


