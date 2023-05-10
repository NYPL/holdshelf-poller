import os
from lib.redis_client import RedisClient
from lib.sierra_db_client import SierraDbClient
from nypl_py_utils.functions.log_helper import create_log
from nypl_py_utils.classes.oauth2_api_client import Oauth2ApiClient
from requests import HTTPError


class Poller:
    """
    Poll Serra db for holdshelf events and trigger notifications to patrons.
    """

    def __init__(self):
        self.logger = create_log('poller')

        self.sierra_client = SierraDbClient()
        self.redis_client = RedisClient()
        self.platform_client = Oauth2ApiClient()

    def poll(self):
        """
        Retrieve holdshelf entries from Sierra, remove processed entries,
        and send notifications for what remains.
        """
        self.logger.info('Starting polling')

        entries = self.sierra_client.holdshelf_entries()

        unfiltered_entries_count = len(entries)
        try:
            entries = list(filter(self.unprocessed, entries))
        except Exception as error:
            self.logger.error(f'Redis read error; Aborting. Error: {error}')
            return
        self.logger.info(
            f'Found {unfiltered_entries_count} holdshelf entries' +
            f' - {len(entries)} of them new')

        if os.environ.get('DISABLE_NOTIFICATIONS', 'false') == 'false':
            self.send_notifications(entries)

        self.logger.info('Done polling')

    def unprocessed(self, entry):
        """Returns true if given entry is not yet processed"""
        return not self.redis_client.get_hold_processed(entry)

    def send_notifications(self, entries):
        """Triggers notifications for array of holdshelf entries"""
        if len(entries) == 0:
            self.logger.info('No notifications to send')
            return

        self.logger.info(
            f'Sending notifications for {len(entries)} unprocessed ' +
            'holdshelf entries')

        for entry in entries:
            path = 'patrons/{}/notify'.format(entry['patron_id'])
            payload = {'type': 'hold-ready', 'sierraHoldId': entry['hold_id']}

            # Post to PatronServices notify endpoint:
            resp = None
            try:
                resp = self.platform_client.post(path, payload)
            except HTTPError as e:
                resp = e.response

            # Assert 200 response:
            if resp and resp.status_code == 200:
                # Mark hold as processed:
                self.redis_client.set_hold_processed(entry)
            elif resp is not None:
                self.logger.error('Unexpected response from PatronServices'
                                  + f' notify endpoint for {path} {payload}'
                                  + f' => {resp.status_code} {resp.content}')
            else:
                self.logger.error('No response from PatronServices'
                                  + f' notify endpoint for {path} {payload}')
