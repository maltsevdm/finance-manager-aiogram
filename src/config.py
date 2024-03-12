import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TOKEN')
MONGO_DB_HOST = os.environ.get('MONGO_DB_HOST')
MONGO_DB_PORT = os.environ.get('MONGO_DB_PORT')
API_BASE_URL = os.environ.get('API_URL')
cookie_key: str = 'CoinKeeper'
