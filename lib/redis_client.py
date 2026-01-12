import os
import redis
import datetime
from lib.logger import logger


class RedisClient:
    def __init__(self):
        self.base_client = self._create_base_client()
        self.logger = logger

    def key_for_hold(self, entry):
        return 'item-status-listener-processed-hold-{}'\
            .format(entry['hold_id'])

    def get_hold_processed(self, entry):
        """Return True if given hold has been processed. False otherwise."""
        key = self.key_for_hold(entry)
        try:
            result = self.base_client.get(key)
        except redis.exceptions.ConnectionError as error:
            self.logger.error(f'Error getting {key} from Redis: {error}')
            raise error

        if result is not None:
            self.logger.debug(
                '  Skip hold {}, already processed on {}'
                .format(entry['hold_id'], result),
                holdId=entry.get('hold_id'),
                itemId=entry.get('item_id')
            )
        return result is not None

    def set_hold_processed(self, entry):
        """Record given holdshelf entry as having been processed"""
        key = self.key_for_hold(entry)
        timestamp = datetime.datetime.utcnow().isoformat()
        self.base_client.set(key, timestamp)
        self.logger.debug(
            'Marked hold {} as processed'.format(entry['hold_id']),
            holdId=entry.get('hold_id'),
            itemId=entry.get('item_id')
        )

    def _create_base_client(self):
        return redis.Redis(
            host=os.environ['REDIS_HOST'],
            port=os.environ['REDIS_PORT'],
            decode_responses=True
        )
