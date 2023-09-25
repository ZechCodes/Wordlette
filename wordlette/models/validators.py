from datetime import time, date, datetime, timezone
from typing import Any, Type, Callable, TypeVar

T = TypeVar("T")


def datetime_validator(value: str | int | float | datetime) -> datetime:
    match value:
        case datetime():
            return value

        case str():
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)

        case int():
            return datetime.fromtimestamp(value, timezone.utc)

        case float():
            return datetime.fromtimestamp(value, timezone.utc)

        case _:
            raise ValueError(f"Cannot convert {value!r} to datetime")


def date_validator(value: str | int | float | date) -> date:
    match value:
        case date():
            return value

        case str():
            return date.fromisoformat(value)

        case int():
            return date.fromtimestamp(value)

        case float():
            return date.fromtimestamp(value)

        case _:
            raise ValueError(f"Cannot convert {value!r} to date")


def time_validator(value: str | int | float | time) -> time:
    match value:
        case time():
            return value

        case str():
            return time.fromisoformat(value)

        case int():
            hour, seconds = divmod(value, 3600)
            minutes, seconds = divmod(seconds, 60)
            return time(hour, minutes, seconds)

        case float():
            hour, seconds = divmod(value, 3600)
            minutes, seconds = divmod(seconds, 60)
            return time(
                int(hour), int(minutes), int(seconds), int((seconds % 1) * 1000000)
            )

        case _:
            raise ValueError(f"Cannot convert {value!r} to time")


def builtin_type_validator(type_: Type[T]) -> Callable[[Any], T]:
    def validate(value: Any) -> T:
        if isinstance(value, type_):
            return value

        return type_(value)

    return validate
