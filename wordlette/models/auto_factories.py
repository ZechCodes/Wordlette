from base64 import urlsafe_b64encode
from datetime import datetime, timezone
from functools import wraps
from typing import TypeVar, Callable, Any
from uuid import uuid4

T = TypeVar("T")


def create_factory(func_or_class: Callable[[], T]) -> Callable[[Any], T]:
    @wraps(func_or_class)
    def create(*_):
        return func_or_class()

    return create


@create_factory
def get_unique_int():
    return uuid4().int


@create_factory
def get_unique_float():
    return float.fromhex(uuid4().hex)


@create_factory
def get_unique_string():
    return urlsafe_b64encode(str(uuid4()).encode()).decode()


@create_factory
def get_current_datetime():
    return datetime.now(timezone.utc)


@create_factory
def get_current_date():
    return get_current_datetime().date()


@create_factory
def get_current_time():
    return get_current_datetime().time()
