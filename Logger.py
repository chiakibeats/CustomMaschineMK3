import logging
from pathlib import Path
from . import Config

logger = logging.getLogger("CustomMaschineMK3")
if Config.LOGGING == True and len(logger.handlers) == 0:
    file_name = Path(__file__).absolute().parent.joinpath("CustomMaschineMK3.log")
    handler = logging.FileHandler(str(file_name))
    handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)d\t%(levelname)s\t%(message)s"))
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)