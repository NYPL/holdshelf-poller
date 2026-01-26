import structlog
from nypl_py_utils.functions.log_helper import create_log

logger = create_log('HoldshelfPoller', json=True)

logger = structlog.wrap_logger(logger, processors=[structlog.contextvars.merge_contextvars])
