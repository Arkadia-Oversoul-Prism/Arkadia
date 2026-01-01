import logging
from logging import Logger
import os

_LOGGER_NAME = "arkadia.weaver"

def get_logger(level: int = logging.INFO, logfile: str | None = None) -> Logger:
    """Return a configured logger for the weaver package.

    If `WEAVER_LOGFILE` is set or a logfile is provided, the logger will write
    to that file in addition to stdout.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        # console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # optional file handler
        logpath = logfile or os.environ.get("WEAVER_LOGFILE")
        if logpath:
            fh = logging.FileHandler(logpath)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        logger.setLevel(level)
        logger.propagate = False
    return logger
