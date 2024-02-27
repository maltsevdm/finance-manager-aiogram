import datetime
from typing import Optional

from sqlalchemy import select, update, delete

from src.database import models
from src.database.db import SessionLocal


def add_user(user_id: int, name: str):
    with SessionLocal() as db:
        db_user = models.User(id=user_id, username=name)
        db.add(db_user)
        db.commit()


def get_user(user_id: int):
    with SessionLocal() as db:
        return db.get_banks(models.User, user_id)


def get_balance(user_id: int) -> int:
    with SessionLocal() as db:
        res = db.get_banks(models.User, user_id)
        return res.balance


def update_balance(user_id: int, new_balance: int):
    with SessionLocal() as db:
        stmt = update(
            models.User).values(balance=new_balance).filter_by(id=user_id)
        db.execute(stmt)
        db.commit()


def add_category(user_id: int, category_group: str, category_name: str):
    with SessionLocal() as db:
        db_category = models.Category(user_id=user_id, name=category_name, type=category_group)
        db.add(db_category)
        db.commit()


def remove_category(user_id: int, category_group: str, category_name: str):
    with SessionLocal() as db:
        stmt = delete(models.Category).filter_by(user_id=user_id, type=category_group, name=category_name)
        db.execute(stmt)
        db.commit()


def get_categories(user_id: int, category_type: Optional[str] = None):
    with SessionLocal() as db:
        query = select(models.Category.name).filter_by(user_id=user_id)
        if category_type:
            query = query.filter_by(type=category_type)
        return db.scalars(query).all()


def add_expense(user_id: int, value: int) -> int:
    with SessionLocal() as db:
        db_expense = models.Operation(
            user_id=user_id,
            type='expense',
            oper_date=datetime.date.today(),
            value=value
        )
        db.add(db_expense)

        balance = get_balance(user_id)
        new_balance = balance - value
        update_balance(user_id, new_balance)

        db.commit()
        return balance


if __name__ == '__main__':
    # Base.metadata.create_all(bind=engine)
    # add_category(508189962, 'Car')
    print(get_categories(508189962))

