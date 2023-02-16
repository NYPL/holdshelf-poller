import os

from nypl_py_utils.functions.config_helper import load_env_file
from nypl_py_utils.functions.log_helper import create_log
from lib.poller import Poller


def main():
    load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')
    logger = create_log(__name__)
    poller = Poller()

    logger.info('Polling...')
    poller.poll()


if __name__ == '__main__':
    main()
