import operator

from wordlette.utils.integer_infinity import Infinity


class Range:
    """An inclusive range implementation that can be unbounded on either end."""

    def __init__(self, start: int | None = None, end: int | None = None, step: int = 1):
        if step == 0:
            raise ValueError("step cannot be 0")

        self._end = Infinity(step < 0) if end is None else end
        self._start = Infinity(step >= 0) if start is None else start
        self._step = step

        self._contains_check = self._create_contains_check()

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def step(self):
        return self._step

    def __contains__(self, n: int):
        return self._contains_check(n)

    def _create_contains_check(self):
        op = operator.ge if self.step > 0 else operator.le

        def contains(n: int):
            if not op(n, self.start):
                return False

            if not op(self.end, n):
                return False

            offset_n = n if isinstance(self.start, Infinity) else n - self.start
            return offset_n % self.step == 0

        return contains
