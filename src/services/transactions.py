import datetime

import httpx

from src.services.config import base_url


class TransactionsService:
    prefix = '/transactions/'

    @classmethod
    async def add(
            cls, token: str, id_category_from: int, id_category_to: int,
            amount: float | int, date: datetime.date, note: str | None = None,
            **kwargs
    ):
        data = {
            'id_category_from': id_category_from,
            'id_category_to': id_category_to,
            'amount': amount,
            'date': date
        }
        if note:
            data['note'] = note
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                base_url + cls.prefix,
                json=data,
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def remove(cls):
        ...

    @classmethod
    async def update(cls):
        ...

    @classmethod
    async def get(
            cls, token,
            date_from: datetime.date | None = None,
            date_to: datetime.date | None = None
    ):
        url = ''
        format = '%Y-%m-%d'
        if date_from:
            date_from_str = date_from.strftime(format)
            url += f'?date_from={date_from_str}'
        if date_to:
            date_to_str = date_to.strftime(format)
            url += f'&date_to={date_to_str}'
        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                base_url + cls.prefix + url,
                cookies={'CoinKeeper': token}
            )
            return response
