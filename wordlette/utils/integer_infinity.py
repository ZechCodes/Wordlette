class Infinity(int):
    def __new__(cls, negative: bool = False):
        positive_inf = super().__new__(cls)
        positive_inf.negative = False

        negative_inf = super().__new__(cls)
        negative_inf.negative = True

        cls.__new__ = lambda _, neg=False: negative_inf if neg else positive_inf
        return cls.__new__(cls, negative)

    def __eq__(self, other):
        return isinstance(other, Infinity) and self.negative == other.negative

    def __lt__(self, other):
        return self.negative

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self.negative

    def __ge__(self, other):
        return self == other or self > other

    def __neg__(self):
        return Infinity(not self.negative)

    def __repr__(self):
        return f"int({'-' * self.negative}Infinity)"
