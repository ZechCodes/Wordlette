from typing import Callable


class Validator:
    def __init__(self, func: Callable):
        self.func = func
