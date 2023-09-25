from base64 import urlsafe_b64encode
from datetime import datetime, timezone
from uuid import uuid4


def create_unique_int_generator(*_):
    def get_unique_int():
        return uuid4().int

    return get_unique_int


def create_unique_float_generator(*_):
    def get_unique_float():
        return float.fromhex(uuid4().hex)

    return get_unique_float


def create_unique_string_generator(*_):
    def get_unique_string():
        return urlsafe_b64encode(str(uuid4()).encode()).decode()

    return get_unique_string


def create_get_current_datetime_func(*_):
    def get_current_datetime():
        return datetime.now(timezone.utc)

    return get_current_datetime


def create_get_current_date_func(*_):
    get_now = create_get_current_datetime_func()

    def get_current_date():
        return get_now().date()

    return get_current_date


def create_get_current_time_func(*_):
    get_now = create_get_current_datetime_func()

    def get_current_time():
        return get_now().time()

    return get_current_time
