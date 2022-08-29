from typing import Any, Callable, ParamSpec, Type, TypeVar
from inspect import signature, Signature
from collections import defaultdict


P = ParamSpec("P")
T = TypeVar("T")


def call(func: Callable[P, T], *args_by_type, **args_by_name) -> T:
    """Calls a function passing in all of the provided args and selectively from the optional_kwargs, only if the
    function has a parameter with the same name."""
    sig = signature(func)
    params_by_name = {
        name: value for name, value in args_by_name.items() if name in sig.parameters
    }
    params_by_type = _build_params_by_type(args_by_type, sig)
    params = sig.bind_partial(**params_by_name | params_by_type)
    return func(*params.args, **params.kwargs)


def _build_params_by_type(args: tuple[Any], sig: Signature) -> dict[str, Any]:
    param_types = _organize_by_param_types(sig)
    return _match_params_to_args(param_types, args)


def _get_param_type_matching_arg(
    param_types: dict[Type, list[str]], arg: Any
) -> Type | None:
    t = type(arg)
    for pt in param_types:
        if issubclass(pt, t) or issubclass(t, pt):
            return pt

    return None


def _match_params_to_args(
    param_types: dict[Type, list[str]], args: tuple[Any]
) -> dict[str, Any]:
    params = {}
    for arg in args:
        param_type = _get_param_type_matching_arg(param_types, arg)
        if param_type and param_types[param_type]:
            params[param_types[param_type].pop(0)] = arg

    return params


def _organize_by_param_types(sig: Signature) -> dict[Type, list[str]]:
    param_types = defaultdict(list)
    for name, param in sig.parameters.items():
        param_types[param.annotation].append(name)

    return param_types