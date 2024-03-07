import secrets
import string
from datetime import date, datetime, timedelta


def find_category_id(name: str, category_list: list[dict]):
    for category in category_list:
        if category['name'] == name:
            return category['id']
    return None


def get_start_month_date(input_date: date | datetime | None = None) -> date:
    if input_date is None:
        input_date = date.today()
    return date(year=input_date.year, month=input_date.month, day=1)


def get_end_month_date(input_date: date | datetime | None = None) -> date:
    if input_date is None:
        input_date = date.today()
    date_start_month = get_start_month_date(input_date)
    date_start_next_month = get_start_month_date(
        date_start_month + timedelta(days=32))
    return date_start_next_month - timedelta(days=1)


def generate_query_params(**kwargs) -> str:
    url = ''
    sym = '?'
    for name, value in kwargs.items():
        url += sym + f'{name}={value}'
        sym = '&'
    return url


def validate_date(date: str) -> str:
    datetime.strptime(date, '%Y-%m-%d')
    return date


def generate_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(12))
