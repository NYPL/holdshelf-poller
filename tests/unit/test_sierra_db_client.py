import pytest

from tests.test_helpers import TestHelpers
from lib.sierra_db_client import SierraDbClient
from nypl_py_utils import (PostgreSQLClient)


class TestSierraDbClient:

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()

    @pytest.fixture
    def mock_pg_execute_query(self, mocker):
        mocker.patch('psycopg_pool.ConnectionPool.connection')
        mocker.patch.object(PostgreSQLClient, 'connect')

        mock = mocker.patch.object(PostgreSQLClient, 'execute_query')
        mock.return_value = [
            {'hold_id': 1, 'other_columns...': None},
            {'hold_id': 2, 'other_columns...': None}
        ]
        return mock

    def test_sierra_db_client(self, mock_pg_execute_query, mocker):
        sierra_db_client = SierraDbClient()

        sierra_db_client.holdshelf_entries()

        mock_pg_execute_query.assert_called_once()
        assert mock_pg_execute_query.call_args.args[0].index(
            'location_code IN (\'mal92\',\'mal98\')'
            ) >= 0

    def test__sql_string_list(self):
        assert SierraDbClient._sql_string_list(['a', 'b', 'c']) \
            == "'a','b','c'"
