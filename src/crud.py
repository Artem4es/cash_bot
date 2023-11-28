from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import joinedload, selectinload

from src.database import async_session_maker, sync_session_maker
from src.models import Users, Payments


def user_exists(tg_id: int) -> bool:
    stmt = select(Users.id).where(Users.tg_id == tg_id)
    with sync_session_maker() as session:
        res = session.execute(stmt)
        return bool(res.scalar())


def add_user(tg_id, username) -> None:
    user = Users(tg_id=tg_id, username=username)
    with sync_session_maker() as session:
        session.add(user)
        session.commit()


def get_users() -> list[Users]:
    stmt = select(Users).order_by(Users.created_at)
    with sync_session_maker() as session:
        res = session.execute(stmt)
        return res.scalars().all()


def add_payment(user_tg_id: int, amount: float) -> None:
    """Добавляем сумму и tg_id в таблицу payments"""
    payment = Payments(amount=amount, user_tg_id=user_tg_id)
    with sync_session_maker() as session:
        session.add(payment)
        session.commit()


def get_period_payments(since: datetime, until: datetime, user_id: Optional[int] = None) -> float:
    if not user_id:
        stmt = select(func.sum(Payments.amount)).where(Payments.created_at.between(since, until))

    else:
        stmt = select(func.sum(Payments.amount)).where(Payments.created_at.between(since, until))

    with sync_session_maker() as session:
        res = session.execute(stmt)
        return res.scalar()


def set_user_owes(tg_id: Optional[int] = None, user_owes: int = 0) -> None:
    """Reset all payments = 0 by default or set certain value"""
    if not tg_id:
        stmt = update(Users).values(user_owes=user_owes)

    else:
        stmt = update(Users).where(Users.tg_id == tg_id).values(user_owes=user_owes)

    with sync_session_maker() as session:
        session.execute(stmt)
        session.commit()


def set_min_pays_since(tg_id: int) -> None:
    """Устанавливаем мин. дату с которой будут считаться платежи (дата рег. первого участника)"""

    stmt = select(func.min(Users.pays_since))
    with sync_session_maker() as session:
        res = session.execute(stmt)
        min_pays_since = res.scalar()

        stmt = update(Users).where(Users.tg_id == tg_id).values(pays_since=min_pays_since)
        session.execute(stmt)
        session.commit()


def delete_db_user(username) -> None:
    """Удаляем пользователя из БД"""
    stmt = delete(Users).where(Users.username == username)
    with sync_session_maker() as session:
        session.execute(stmt)
        session.commit()
    # self.cursor.execute('DELETE FROM "users" WHERE "username"=?',(username,))
    # return self.conn.commit()


def get_db_all_payments():
    """Все платежи в базе на текущий момент"""
    stmt = select(Users.username, Payments.amount, Payments.created_at).join(Payments, Payments.user_tg_id == Users.tg_id)   # не понятно как получить обе таблицы
    with sync_session_maker() as session:
        res = session.execute(stmt)
        return res.all()


def delete_payments() -> None:
    """Delete all payments"""
    stmt = delete(Payments)
    with sync_session_maker() as session:
        session.execute(stmt)
        session.commit()
