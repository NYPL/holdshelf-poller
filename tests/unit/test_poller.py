import os
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
        mock = mocker.patch('lib.poller.Oauth2ApiClient.post')
        mock.return_value = mocker.MagicMock()
        mock.return_value.status_code = 200
        return mock

    @pytest.fixture
    def platform_api_client_post_failed(self, mocker):
        mock = mocker.patch('lib.poller.Oauth2ApiClient.post')
        mock.return_value = mocker.MagicMock()
        mock.return_value.status_code = 500
        return mock

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

    def test_patron_notification_allowed(self):
        # With no ONLY_NOTIFY_PATRON_IDS, assert patron 10 allowed:
        assert Poller().patron_notification_allowed({'hold_id': 1, 'patron_id': 10}) is True

        # With ONLY_NOTIFY_PATRON_IDS='20,10', assert patron 10 allowed:
        os.environ['ONLY_NOTIFY_PATRON_IDS'] = '20,10'
        assert Poller().patron_notification_allowed({'hold_id': 1, 'patron_id': 10}) is True

        del os.environ['ONLY_NOTIFY_PATRON_IDS']

    def test_patron_notification_disallowed(self):
        # With ONLY_NOTIFY_PATRON_IDS='20', assert patron 10 disallowed:
        os.environ['ONLY_NOTIFY_PATRON_IDS'] = '20'
        assert Poller().patron_notification_allowed({'hold_id': 1, 'patron_id': 10}) is False

        # With ONLY_NOTIFY_PATRON_IDS='30,20', assert patron 10 disallowed:
        os.environ['ONLY_NOTIFY_PATRON_IDS'] = '30,20'
        assert Poller().patron_notification_allowed({'hold_id': 1, 'patron_id': 10}) is False

        del os.environ['ONLY_NOTIFY_PATRON_IDS']

    def test_filter_out_disallowed(self):
        # With no ONLY_NOTIFY_PATRON_IDS, assert patron 10 allowed:
        entries = [{'hold_id': 1, 'patron_id': 10}]
        assert Poller().filter_out_disallowed(entries)[0]['patron_id'] == 10

        # With ONLY_NOTIFY_PATRON_IDS='20,10', assert patron 10 disallowed:
        os.environ['ONLY_NOTIFY_PATRON_IDS'] = '20'
        assert len(Poller().filter_out_disallowed(entries)) == 0

        del os.environ['ONLY_NOTIFY_PATRON_IDS']

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

        # Verify we post to PatronServices Notify endpoint:
        platform_api_client_post.assert_called_once_with(
                'patrons/9001/notify', {'sierraHoldId': 1, 'type': 'hold-ready'})
        # Verify we record hold processed in Redis:
        redis_set_hold_processed.assert_called_once_with(mock_holds[0])

    def test_send_notifications_failed(self, redis_set_hold_processed,
                                       platform_api_client_post_failed):
        mock_holds = [{'hold_id': 1, 'patron_id': 9001}]
        Poller().send_notifications(mock_holds)

        # Verify we post to PatronServices Notify endpoint:
        platform_api_client_post_failed.assert_called_once_with(
                'patrons/9001/notify', {'sierraHoldId': 1, 'type': 'hold-ready'})
        # Verify we DO NOT record hold processed in Redis:
        redis_set_hold_processed.assert_not_called()
