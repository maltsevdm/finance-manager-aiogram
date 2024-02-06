import httpx
from httpx import Response

from src.services.config import base_url


class CategoriesService:
    prefix = '/categories/'

    @classmethod
    async def add(cls, token: str, name: str, group: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                base_url + cls.prefix,
                json={'name': name, 'group': group},
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def remove(cls, token: str, id: int) -> Response:
        async with httpx.AsyncClient() as ac:
            response = await ac.delete(
                base_url + cls.prefix + str(id),
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def get(cls, token: str, group: str) -> Response:
        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                base_url + cls.prefix + f'?group={group}',
                cookies={'CoinKeeper': token}
            )
            return response

    @classmethod
    async def update(
            cls, token: str, id: int, name: str | None = None,
            amount: float | None = None
    ) -> Response:
        data = {}
        if name is not None:
            data['name'] = name
        if amount is not None:
            data['amount'] = amount
        async with httpx.AsyncClient() as ac:
            response = await ac.patch(
                base_url + cls.prefix + str(id),
                json=data,
                cookies={'CoinKeeper': token}
            )
            return response


