from enum import Enum, auto


class AuthSecurityLevel(int, Enum):
    UNSAFE = auto()
    BASIC = auto()
    SECURE = auto()
    VERY_SECURE = auto()
