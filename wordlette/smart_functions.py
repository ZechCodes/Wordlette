from typing import Callable, ParamSpec, TypeVar
from inspect import signature


P = ParamSpec("P")
T = TypeVar("T")


def call(func: Callable[P, T], *args, **optional_kwargs) -> T:
    """Calls a function passing in all of the provided args and selectively from the optional_kwargs, only if the
    function has a parameter with the same name."""
    sig = signature(func)
    provided_params = {
        name: value for name, value in optional_kwargs.items() if name in sig.parameters
    }
    params = sig.bind_partial(*args, **provided_params)
    return func(*params.args, **params.kwargs)
