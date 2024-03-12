import datetime
from abc import ABC

import httpx
from httpx import Response

from src.config import API_BASE_URL
from src.utils.utils import generate_query_params


class CategoriesService(ABC):
    prefix: str

    @classmethod
    async def create(cls, token: str, name: str, group: str, **data):
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                API_BASE_URL + cls.prefix,
                json={'name': name, 'group': group, **data},
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def read(
            cls, token: str,
            group: str | None = None,
            date_from: datetime.date | None = None,
            date_to: datetime.date | None = None
    ) -> Response:
        url = cls.prefix
        params = {}
        if group is not None:
            params['group'] = group
        if date_from is not None:
            params['date_from'] = date_from
        if date_to is not None:
            params['date_to'] = date_to
        url += generate_query_params(**params)
        # if group:
        #     url += f'?group={group}'
        # if date_from is not None:
        #     sym = '&' if '?' in url else '?'
        #     url += f'{sym}date_from={date_from}'
        # if date_to is not None:
        #     sym = '&' if '?' in url else '?'
        #     url += f'{sym}date_to={date_to}'
        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                API_BASE_URL + url,
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def update(
            cls, token: str, id: int, **data
    ) -> Response:
        async with httpx.AsyncClient() as ac:
            response = await ac.patch(
                API_BASE_URL + cls.prefix + str(id),
                json=data,
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def delete(cls, token: str, id: int) -> Response:
        async with httpx.AsyncClient() as ac:
            response = await ac.delete(
                API_BASE_URL + cls.prefix + str(id),
                cookies={'CoinKeeper': token}
            )
            return response
