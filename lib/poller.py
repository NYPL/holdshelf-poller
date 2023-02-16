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
        self.logger.debug('Starting polling')

        entries = self.sierra_client.holdshelf_entries()
        entries = [entry for entry in entries if self.unprocessed(entry)]

        self.send_notifications(entries)

        self.logger.debug('Done polling')

    def unprocessed(self, entry):
        return not self.redis_client.get_hold_processed(entry)

    def send_notifications(self, entries):
        if len(entries) == 0:
            print('No notifications to send')
            return

        print('Report on holdshelf events:')
        for entry in entries:
            print('  {}'.format(entry))
            self.redis_client.set_hold_processed(entry)
