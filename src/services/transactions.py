import datetime

import httpx
from httpx import Response

from src.services.config import base_url
from src.utils.utils import generate_query_params

def filter_by_none(data: dict):
    return dict(filter(lambda x: x[1] is not None, data.items()))


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
    async def delete(cls, token: str, id: int) -> Response:
        async with httpx.AsyncClient() as ac:
            response = await ac.delete(
                base_url + cls.prefix + str(id),
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def update(cls, token: str, id: int, data: dict) -> Response:
        async with httpx.AsyncClient() as ac:
            response = await ac.patch(
                base_url + cls.prefix + str(id),
                json=data,
                cookies={'CoinKeeper': token}
            )
            return response

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
    async def get_sum(
            cls,
            token,
            group: str,
            date_from: datetime.date | None = None,
            date_to: datetime.date | None = None,
            status: str | None = None
    ):
        params = {
            'group': group,
            'date_from': date_from,
            'date_to': date_to,
            'status': status
        }
        params = filter_by_none(params)

        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                base_url + cls.prefix + 'sum' + generate_query_params(**params),
                cookies={'CoinKeeper': token}
            )
            return response
