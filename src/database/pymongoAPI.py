from pymongo import MongoClient

from src import config


class MongoDB(object):
    def __init__(
            self,
            host: str = 'localhost',
            port: int = 27017,
            db_name: str = None,
            collection: str = None
    ):
        self._client = MongoClient(f'mongodb://{host}:{port}')
        self._collection = self._client[db_name][collection]

    def create_user(self, user: dict):
        try:
            if self._collection.find_one(
                    {'username': user.get('username')}) is None:
                self._collection.insert_one(user)
                print(f'Added New user: {user.get("username")}')
            else:
                print(f'User: {user.get("username")} in collection')
        except Exception as ex:
            print('[create_user] Some problem...')
            print(ex)

    def get_all_users(self):
        try:
            return self._collection.find()
        except Exception as ex:
            print('[get_all] Some problem...')
            print(ex)

    def find_by_user_id(self, user_id: int) -> dict | None:
        try:
            return self._collection.find_one({'user_id': user_id})
        except Exception as ex:
            print('[find_by_username] Some problem...')
            print(ex)

    def get_field_by_user_id(self, user_id: int, field: str):
        try:
            return self.find_by_user_id(user_id)[field]
        except Exception as ex:
            print('[field_by_user_id] Some problem...')
            print(ex)

    def change_user(self, user_id: str, key: str, value: str):
        try:
            if self._collection.find_one({'user_id': user_id}) is not None:
                self._collection.update_one(
                    filter={'user_id': user_id},
                    update={'$set': {key: value}}
                )
            else:
                print(f'User: {user_id} not find')
        except Exception as ex:
            print('[change_user] Some problem...')
            print(ex)


users_db = MongoDB(
    host=config.MONGO_DB_HOST,
    port=config.MONGO_DB_PORT,
    db_name='tg_bot_fm',
    collection='user'
)
