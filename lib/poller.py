from lib.redis_client import RedisClient
from lib.sierra_db_client import SierraDbClient
from nypl_py_utils.functions.log_helper import create_log
from nypl_py_utils import Oauth2ApiClient


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
        """Retrieve holdshelf entries from Sierra, remove processed entries,
        and send notifications for what remains.
        """
        self.logger.info('Starting polling')

        entries = self.sierra_client.holdshelf_entries()

        self.logger.info(f'Found {len(entries)} holdshelf entries')
        try:
            entries = list(filter(self.unprocessed, entries))
        except Exception as error:
            self.logger.error(f'Redis read error; Aborting. Error: {error}')
            return

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
            payload = {'type': 'hold-ready', 'holdId': entry['hold_id']}

            self.logger.debug(f'Posting to {path}: {payload}')
            self.logger.info(f'Posting to {path}: {payload} => {self.platform_client.post}')
            self.platform_client.post(path, payload)

            self.redis_client.set_hold_processed(entry)
