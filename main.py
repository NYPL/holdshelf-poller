import os

from nypl_py_utils.functions.config_helper import load_env_file
from lib.poller import Poller


def main():
    load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')

    poller = Poller()
    poller.poll()


if __name__ == '__main__':
    main()
