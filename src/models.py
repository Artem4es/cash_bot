import asyncio
from datetime import datetime

from sqlalchemy import Table, Column, Integer, String, ForeignKey, func, text
from src.database import Base
from sqlalchemy.orm import Mapped, mapped_column


class Users(Base):  # не переносил public_message
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    user_owes: Mapped[int] = mapped_column(server_default="0")               # тут изящнее???
    pays_since: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))



class Payments(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))   # тут изящнее???
    user_tg_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))


#####################################################


from src.database import async_engine


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# asyncio.run(create_tables())
