import os

from nypl_py_utils.functions.config_helper import load_env_file
from lib.poller import Poller

_has_run_init = None


def init():
    global _has_run_init
    if not _has_run_init:
        load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')
        _has_run_init = True


def handle_event(event=None, context=None):
    init()

    Poller().poll()


if __name__ == '__main__':
    handle_event()
