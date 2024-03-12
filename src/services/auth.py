import httpx

from src.config import API_BASE_URL


class AuthService:

    @staticmethod
    async def login(email: str, password: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                API_BASE_URL + '/auth/jwt/login',
                data={'username': email, 'password': password}
            )
            return response

    @staticmethod
    async def register(email: str, password: str, username: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.post(
                API_BASE_URL + '/auth/register',
                json={
                    'email': email,
                    'password': password,
                    'username': username
                }
            )
            return response

    @staticmethod
    async def get_profile(token: str):
        async with httpx.AsyncClient() as ac:
            response = await ac.get(
                API_BASE_URL + '/users/me',
                cookies={'value': token}
            )
            return response
