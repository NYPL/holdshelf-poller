"""

This is a script for generating test holdshelf events in the local psql db.

Usage:
    AWS_PROFILE=nypl-digital-dev ENVIRONMENT=development \
        python create_test_data.py

"""

import os
import datetime

from nypl_py_utils import PostgreSQLClient, PostgreSQLClientError
from nypl_py_utils.functions.config_helper import load_env_file
from nypl_py_utils.functions.log_helper import create_log

HOLDS = [
    [1, 10001, 'i', 'YYYY-MM-DDT08:11:01', 'mal'],
    [2, 10002, 'i', 'YYYY-MM-DDT08:31:01', 'mal']
]

ITEMS = [
    (10001, 101, 'maf92'),
    (10002, 102, 'maf92')
]


class CreateTestData:

    def connect(self):
        load_env_file(os.environ['ENVIRONMENT'], 'config/development.yaml')
        self.sierra_client = PostgreSQLClient(
            '127.0.0.1',
            os.environ['SIERRA_DB_PORT'],
            os.environ['SIERRA_DB_NAME'],
            os.environ['SIERRA_DB_USER'],
            os.environ['SIERRA_DB_PASSWORD']
        )
        self.sierra_client.connect()
        self.logger = create_log('redis_client')

    def disconnect(self):
        self.sierra_client.close_connection()

    def insert_data(self, table, row):
        value_placeholders_str = ', '.join(['%s' for n in range(len(row))])
        query = 'INSERT INTO sierra_view.{} VALUES ({})'.format(
            table, value_placeholders_str)
        self.logger.debug(f' => {query} < {row}')
        self.sierra_client.execute_query(query, query_params=row,
                                         is_write_query=True)

    def db_query(self, query, data=None):
        with self.sierra_client.pool.connection() as conn:
            try:
                conn.execute(query, data)
            except Exception as e:
                conn.rollback()
                self.logger.error(
                    ('Error executing database query \'{query}\': '
                     '{error}').format(query=query, error=e))
                raise PostgreSQLClientError(
                    ('Error executing database query \'{query}\': '
                     '{error}').format(query=query, error=e)) from None

    def create_test_data(self):
        self.connect()

        self.logger.info('Truncating tables')
        for table in ['hold', 'item_view']:
            self.db_query('TRUNCATE TABLE sierra_view.{}'.format(table))

        self.logger.info('Filling tables')
        for row in ITEMS:
            self.insert_data('item_view', row)
        for row in HOLDS:
            current_date = datetime.date.today().isoformat()
            row[3] = row[3].replace('YYYY-MM-DD', current_date)
            self.insert_data('hold', row)

        self.disconnect()


if __name__ == '__main__':
    CreateTestData().create_test_data()
