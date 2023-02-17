import pytest
from freezegun import freeze_time

from tests.test_helpers import TestHelpers
from lib.redis_client import RedisClient


@freeze_time('2023-01-01 01:00:00')
class TestRedisClient:

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()

    @pytest.fixture
    def mock_redis_get(self, mocker):
        mock = mocker.patch('redis.Redis.get')
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_redis_set(self, mocker):
        return mocker.patch('redis.Redis.set')

    def test_key_for_hold(self):
        assert RedisClient().key_for_hold({'hold_id': 10}) \
            == 'item-status-listener-processed-hold-10'

    def test_hold_get_processed(self, mock_redis_get, mocker):
        redis = RedisClient()

        assert redis.get_hold_processed({'hold_id': 1}) is False

        mock_redis_get.return_value = '12321'
        assert redis.get_hold_processed({'hold_id': 1}) is True

    def test_hold_set_processed(self, mock_redis_get, mock_redis_set, mocker):
        redis = RedisClient()

        redis.set_hold_processed({'hold_id': 1}) is False

        assert mock_redis_set.call_args.args \
            == ('item-status-listener-processed-hold-1', '2023-01-01T01:00:00')
