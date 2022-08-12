from types import NoneType

import psycopg2  # == psycopg2-binary==2.9.3
from psycopg2 import Error


class PostGISConnector:
    def __init__(self, host, port, user, password, database: str = 'awvinfra'):
        self.connection = psycopg2.connect(user=user,
                                           password=password,
                                           host=host,
                                           port=port,
                                           database=database)
        self.connection.autocommit = False
        self.db = database

    def perform_query(self, query: str):
        cursor = self.connection.cursor()
        result = cursor.execute(query).fetchmany()
        cursor.close()
        return result

    def get_params(self):
        cursor = self.connection.cursor()
        try:
            keys = ['page', 'event_uuid', 'pagesize', 'fresh_start', 'sync_step', 'pagingcursor', 'last_update_utc']
            keys_in_query = ', '.join(keys)
            cursor.execute(f'SELECT {keys_in_query} FROM public.params')
            record = cursor.fetchone()
            params = dict(zip(keys, record))
            cursor.close()
            return params
        except Error as error:
            if '"public.params" does not exist' in error.pgerror:
                cursor.close()
                self.connection.rollback()
                return None
            else:
                print("Error while connecting to PostgreSQL", error)
                cursor.close()
                self.connection.rollback()
                raise error

    def close(self):
        self.connection.close()

    def commit_transaction(self):
        self.connection.commit()


class SinglePostGISConnector:
    postgis_connector: PostGISConnector | NoneType = None

    @classmethod
    def init(cls, host: str = '', port:str = '', user: str = '', password: str = '', database: str = 'awvinfra'):
        cls.postgis_connector = PostGISConnector(host, port, user, password, database)

    @classmethod
    def get_connector(cls) -> PostGISConnector:
        if cls.postgis_connector is None:
            raise RuntimeError('Run the init method of this class first')
        return cls.postgis_connector
