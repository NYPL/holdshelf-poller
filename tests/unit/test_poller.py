import pytest

from tests.test_helpers import TestHelpers
from lib.poller import Poller


class TestPoller:

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()

    @pytest.fixture
    def redis_set_hold_processed(self, mocker):
        return mocker.patch('lib.poller.RedisClient.set_hold_processed')

    @pytest.fixture
    def redis_get_hold_processed(self, mocker):
        mock = mocker.patch('lib.poller.RedisClient.get_hold_processed')
        mock.return_value = False
        return mock

    @pytest.fixture
    def sierra_holdshelf_entries(self, mocker):
        return mocker.patch('lib.poller.SierraDbClient.holdshelf_entries')

    @pytest.fixture
    def platform_api_client_post(self, mocker):
        return mocker.patch('lib.poller.Oauth2ApiClient.post')

    def test_unprocessed_uses_redis(self, redis_get_hold_processed):
        # If RedisClient.get_hold_processed() returns false, Poller considers
        # it unprocessed
        assert Poller().unprocessed({'hold_id': 1}) is True
        redis_get_hold_processed.assert_called_once_with({'hold_id': 1})

        # If RedisClient.get_hold_processed() returns true, Poller considers
        # it processed
        redis_get_hold_processed.return_value = True
        assert Poller().unprocessed({'hold_id': 2}) is False
        redis_get_hold_processed.assert_called_with({'hold_id': 2})

    def test_poll(self, sierra_holdshelf_entries, redis_get_hold_processed,
                  mocker):
        send_notifications = mocker.patch(
                'lib.poller.Poller.send_notifications')
        mock_holds = [{'hold_id': 1, 'patron_id': 9001}]
        sierra_holdshelf_entries.return_value = mock_holds

        Poller().poll()

        # Verify poller fetches holdshelf entries:
        sierra_holdshelf_entries.assert_called_once()
        # Verify poller passes those entries on for notification:
        send_notifications.assert_called_once_with(mock_holds)

    def test_send_notifications(self, redis_set_hold_processed,
                                platform_api_client_post):
        mock_holds = [{'hold_id': 1, 'patron_id': 9001}]
        Poller().send_notifications(mock_holds)

        # Verify we record hold processed in Redis:
        redis_set_hold_processed.assert_called_once_with(mock_holds[0])
        # Verify we post to PatronServices Notify endpoint:
        platform_api_client_post.assert_called_once_with(
                'patrons/9001/notify', {'holdId': 1, 'type': 'hold-ready'})
