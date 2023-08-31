from asyncio import iscoroutinefunction
from functools import wraps, partial
from inspect import signature, get_annotations
from typing import TypeVar, Callable, get_origin, Annotated

from bevy import get_repository
from bevy.injectors.functions import _get_function_namespace

from wordlette.at_annotateds import AtAnnotation

T = TypeVar("T", bound=Callable)


def inject(func: T) -> T:
    sig = signature(func)
    annotations = _get_annotations(func)
    # Determine which parameters have a declared dependency
    inject_parameters = {
        name: annotations[name]
        for name, parameter in sig.parameters.items()
        if name in annotations and _is_at_annotation_type(annotations[name])
    }

    @wraps(func)
    def injector(*args, **kwargs):
        params = sig.bind_partial(*args, **kwargs)
        # Get instances from the repo to fill all missing dependency parameters
        params.arguments |= {
            name: get_repository().get(annotation)
            for name, annotation in inject_parameters.items()
            if name not in params.arguments
        }
        return func(*params.args, **params.kwargs)

    injector.injected_params = inject_parameters
    if iscoroutinefunction(func):

        @wraps(func)
        async def async_injector(*args, **kwargs):
            return await injector(*args, **kwargs)

        return async_injector

    return injector


class AutoInject:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name in dir(cls):
            try:
                attr = getattr(cls, name)
            except AttributeError:
                continue

            if not name.endswith("__") and _needs_injector(attr):
                setattr(cls, name, inject(attr))


class Dependency(AtAnnotation):
    def strategy(self, type_, _):
        return partial(get_repository().get, type_)


def _get_annotations(func):
    ns = _get_function_namespace(func)
    return get_annotations(func, globals=ns, eval_str=True)


def _is_at_annotation_type(annotation) -> bool:
    origin = get_origin(annotation)
    if origin is not Annotated:
        return False

    return True


def _needs_injector(attr):
    if isinstance(attr, type):
        return False

    if not callable(attr):
        return False

    if hasattr(attr, "injected_params"):
        return False

    return any(
        _is_at_annotation_type(annotation)
        for annotation in _get_annotations(attr).values()
    )


dependency = Dependency
