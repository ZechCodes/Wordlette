from typing import Callable

from wordlette.base_exceptions import BaseWordletteException


class ValidationError(BaseWordletteException):
    pass


class Validator:
    def __init__(self, func: Callable):
        self.func = func
