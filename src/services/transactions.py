import datetime

import httpx

from src.services.config import base_url


class TransactionsService:
    prefix = '/transactions/'

    @classmethod
    async def add(
            cls, token: str, group: str, id_bank: int, id_destination: int,
            amount: float | int, date: datetime.date, note: str = ''
    ):
        data = {
            'group': group,
            'bank_id': id_bank,
            'destination_id': id_destination,
            'amount': amount,
            'date': date,
            # 'note': note
        }

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
            cls,
            token,
            limit: int = 5,
            offset: int = 0,
            date_from: datetime.date | None = None,
            date_to: datetime.date | None = None
    ):
        url = f'?limit={limit}&offset={offset}'
        format = '%Y-%m-%d'
        if date_from:
            date_from_str = date_from.strftime(format)
            url += f'&date_from={date_from_str}'
        if date_to:
            date_to_str = date_to.strftime(format)
            url += f'&date_to={date_to_str}'

        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                base_url + cls.prefix + url,
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def get_sum(cls, token, group: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                base_url + cls.prefix + f'sum?group={group}',
                cookies={'CoinKeeper': token}
            )
            return response
