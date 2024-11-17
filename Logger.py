import logging
from pathlib import Path
from . import Config

from datetime import datetime, timedelta, timezone


class ISOTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt = None):
        time = datetime.fromtimestamp(record.created)
        time_string = time.isoformat(timespec = "microseconds")

        return time_string

logger = logging.getLogger("CustomMaschineMK3")
if Config.LOGGING == True and len(logger.handlers) == 0:
    file_name = Path(__file__).absolute().parent.joinpath("CustomMaschineMK3.log")
    handler = logging.FileHandler(str(file_name))
    
    formatter = ISOTimeFormatter("%(asctime)s\t%(levelname)s\t%(message)s") # logging.Formatterの代わりに自作のクラスを使う

    handler.setFormatter(formatter)

    level_table = {
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.FATAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARN,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }

    logger.setLevel(level_table.get(Config.LOG_LEVEL, logging.INFO))
    logger.addHandler(handler)