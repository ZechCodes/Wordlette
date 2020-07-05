from functools import partial
import logging


class Logging:
    def __init__(self, name: str = "WORDLETTE"):
        self.logger = logging.getLogger("wordlette")
        self.name = name

        self.info = partial(self.log, logging.INFO)
        self.debug = partial(self.log, logging.DEBUG)
        self.warning = partial(self.log, logging.WARNING)
        self.error = partial(self.log, logging.ERROR)
        self.critical = partial(self.log, logging.CRITICAL)

    def log(self, level: int, message: str, *args, **kwargs):
        self.logger.log(level, f"{self.name}: {message}", *args, **kwargs)
