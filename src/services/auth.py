import httpx

from src.services.config import base_url


class AuthService:

    @staticmethod
    async def login(email: str, password: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                base_url + '/auth/jwt/login',
                data={'username': email, 'password': password}
            )
            return response

    @staticmethod
    async def register(email: str, password: str, username: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                base_url + '/auth/register',
                data={
                    'username': username,
                    'password': password,
                    'email': email
                }
            )
            return response

    @staticmethod
    async def get_profile(token: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                base_url + '/users/me',
                cookies={'value': token}
            )
            return response
