# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

import logging
from pathlib import Path
from . import config

from datetime import datetime, timedelta, timezone

class ISOTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt = None):
        time = datetime.fromtimestamp(record.created)
        time_string = time.isoformat(timespec = "microseconds")

        return time_string

logger = logging.getLogger("CustomMaschineMK3")
"""
Global logger for this script.

Log messages also send to `Log.txt` in Live's preference directory.
"""

if config.LOGGING == True and len(logger.handlers) == 0:
    file_name = Path(__file__).absolute().parent.joinpath("CustomMaschineMK3.log")
    handler = logging.FileHandler(str(file_name))
    
    # Use custom formatter to output accurate timestamp
    formatter = ISOTimeFormatter("%(asctime)s\t%(levelname)s\t%(message)s")

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

    logger.setLevel(level_table.get(config.LOG_LEVEL, logging.INFO))
    logger.addHandler(handler)

else:
    # Set to max level for eliminating log outputs
    logger.setLevel(logging.CRITICAL)
