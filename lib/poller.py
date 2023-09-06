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

    def filter_out_processed(self, entries):
        """
        Given an array of holdshelf entries , returns the subset of entries that are not yet processed
        """
        unfiltered_entries_count = len(entries)
        try:
            entries = list(filter(self.unprocessed, entries))
        except Exception as error:
            self.logger.error(f'Redis read error; Aborting. Error: {error}')
            return
        self.logger.info(
            f'Found {unfiltered_entries_count} holdshelf entries' +
            (f' - {len(entries)} of them new' if len(entries) != 0 else ''))
        return entries

    def filter_out_disallowed_and_mark_processed(self, entries):
        """
        Given an array of holdshelf entries, returns subset that are allowed to be processed based on
        ONLY_NOTIFY_PATRON_IDS config, if set
        """
        disallowed = [entry for entry in entries if not self.patron_notification_allowed(entry)]
        if len(disallowed) > 0:
            # Let's mark them as processed so that when we remove the ONLY_NOTIFY_PATRON_IDS config,
            # we don't immediately process all active holdshelf entries found in the last 48 hours.
            # (i.e. if a hold is currently barred due to a ONLY_NOTIFY_PATRON_IDS config, we should
            # _never_ process it, even after removing said config.)
            for entry in disallowed:
                self.redis_client.set_hold_processed(entry)

            disallowed_patrons = [entry['patron_id'] for entry in disallowed]
            self.logger.info(f'Removing {len(disallowed_patrons)} holdshelf entries'
                             f' for disallowed patrons: {disallowed_patrons}')

        entries = [e for e in entries if self.patron_notification_allowed(e)]
        return entries

    def poll(self):
        """
        Retrieve holdshelf entries from Sierra, remove processed entries,
        and send notifications for what remains.
        """
        self.logger.info('Starting polling')

        entries = self.sierra_client.holdshelf_entries()

        # Remove entries we have already processed:
        entries = self.filter_out_processed(entries)
        # Remove entries we're configured to ignore (and mark them as processed):
        entries = self.filter_out_disallowed_and_mark_processed(entries)

        if len(entries) > 0:
            if os.environ.get('DISABLE_NOTIFICATIONS', 'False') == 'False':
                self.send_notifications(entries)
            else:
                self.logger.info('Skipping sending notifications because DISABLE_NOTIFICATIONS is enabled')

        self.logger.info('Done polling')

    def unprocessed(self, entry):
        """Returns true if given entry is not yet processed"""
        return not self.redis_client.get_hold_processed(entry)

    def patron_notification_allowed(self, entry):
        allowed_ids_str = os.environ.get('ONLY_NOTIFY_PATRON_IDS', '')
        # The patron is allowed if there's no configured ONLY_NOTIFY_PATRON_IDS
        if allowed_ids_str == '':
            return True

        # The patron is allowed if a configured ONLY_NOTIFY_PATRON_IDS that contains the patron_id:
        allowed_ids = allowed_ids_str.split(',')
        patron_id = entry['patron_id']
        if len(allowed_ids) == 0 or str(patron_id) in allowed_ids:
            return True

        # There's a configured ONLY_NOTIFY_PATRON_IDS, but patron_id isn't in it:
        return False

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
