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

HOLDS = [
    [1, 10001, 'i', 'YYYY-MM-DDT08:11:01', 'mal'],
    [2, 10002, 'i', 'YYYY-MM-DDT08:31:01', 'mal']
]

ITEMS = [
    (10001, 101, 'maf92'),
    (10002, 102, 'maf92')
]

sierra_client = None


def connect():
    global sierra_client

    load_env_file(os.environ['ENVIRONMENT'], 'config/development.yaml')
    sierra_client = PostgreSQLClient(
        '127.0.0.1',
        os.environ['SIERRA_DB_PORT'],
        os.environ['SIERRA_DB_NAME'],
        os.environ['SIERRA_DB_USER'],
        os.environ['SIERRA_DB_PASSWORD']
    )
    sierra_client.connect()


def disconnect():
    global sierra_client
    sierra_client.close_connection()


def insert_data(table, row):
    global sierra_client

    values_str = ', '.join(['%s' for n in range(len(row))])
    query = 'INSERT INTO sierra_view.{} VALUES ({})'.format(table, values_str)
    print(' => {} < {}'.format(query, row))
    db_query(query, row)


def db_query(query, data=None):
    with sierra_client.pool.connection() as conn:
        try:
            conn.execute(query, data)
        except Exception as e:
            conn.rollback()
            print(
                ('Error executing database query \'{query}\': '
                 '{error}').format(query=query, error=e))
            raise PostgreSQLClientError(
                ('Error executing database query \'{query}\': '
                 '{error}').format(query=query, error=e)) from None


def create_test_data():
    connect()

    print('Truncating tables')
    for table in ['hold', 'item_view']:
        db_query('TRUNCATE TABLE sierra_view.{}'.format(table))

    print('Filling tables')
    for row in ITEMS:
        insert_data('item_view', row)
    for row in HOLDS:
        current_date = datetime.datetime.utcnow().isoformat().split('T')[0]
        row[3] = row[3].replace('YYYY-MM-DD', current_date)
        insert_data('hold', row)

    disconnect()


if __name__ == '__main__':
    create_test_data()
