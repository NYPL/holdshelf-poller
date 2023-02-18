from lib.redis_client import RedisClient
from lib.sierra_db_client import SierraDbClient
from nypl_py_utils.functions.log_helper import create_log


class Poller:
    """
    Poll Serra db for holdshelf events and trigger notifications to patrons.
    """

    def __init__(self):
        self.logger = create_log('poller')

        self.sierra_client = SierraDbClient()
        self.redis_client = RedisClient()

    def poll(self):
        """Retrieve holdshelf entries from Sierra, remove processed entries,
        and send notifications for what remains.
        """
        self.logger.info('Starting polling')

        entries = self.sierra_client.holdshelf_entries()

        self.logger.info(f'Found {len(entries)} holdshelf entries')
        try:
            entries = [entry for entry in entries if self.unprocessed(entry)]
        except Exception as error:
            self.logger.error(f'Redis read error; Aborting. Error: {error}')
            return

        self.send_notifications(entries)

        self.logger.info('Done polling')

    def unprocessed(self, entry):
        """Returns true if given entry is not yet processed"""
        return not self.redis_client.get_hold_processed(entry)

    def send_notifications(self, entries):
        """Send notifications for array of holdshelf entries"""
        if len(entries) == 0:
            self.logger.info('No notifications to send')
            return

        self.logger.info(
            f'Sending notifications for {len(entries)} unprocessed ' +
            'holdshelf entries')

        print('Report on holdshelf events:')
        for entry in entries:
            print('  {}'.format(entry))
            self.redis_client.set_hold_processed(entry)
