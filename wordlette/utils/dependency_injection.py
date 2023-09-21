from asyncio import iscoroutinefunction
from functools import wraps, partial
from inspect import signature, get_annotations
from typing import TypeVar, Callable, get_origin, Annotated, get_args

from bevy import get_repository
from bevy.injectors.functions import _get_function_namespace

from wordlette.utils.at_annotateds import AtAnnotation

T = TypeVar("T", bound=Callable)


def inject_dependencies(func: T) -> T:
    sig = signature(func)
    annotations = _get_annotations(func)
    # Determine which parameters have a declared inject
    inject_parameters = {
        name: annotations[name]
        for name, parameter in sig.parameters.items()
        if name in annotations and _is_at_annotation_type(annotations[name])
    }

    @wraps(func)
    def injector(*args, **kwargs):
        params = sig.bind_partial(*args, **kwargs)
        # Get instances from the repo to fill all missing inject parameters
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

            if not name.endswith("__") and _needs_injector(attr, {cls.__name__: cls}):
                setattr(cls, name, inject_dependencies(attr))

        for name, value in get_annotations(cls).items():
            if get_origin(value) is Annotated:
                hint, annotation = get_args(value)
                if isinstance(annotation, Dependency):
                    annotation.injector = annotation.strategy(hint)
                    setattr(cls, name, annotation)


class Dependency(AtAnnotation):
    def __init__(self):
        super().__init__()
        self.injector = None

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return self.injector()

    def strategy(self, type_, *_):
        return partial(get_repository().get, type_)


def _get_annotations(func, ns=None):
    ns = (ns or {}) | _get_function_namespace(func)
    try:
        return get_annotations(func, globals=ns, eval_str=True)
    except NameError as exc:
        raise NameError(f"Couldn't process annotations on {func.__qualname__}") from exc


def _is_at_annotation_type(annotation) -> bool:
    origin = get_origin(annotation)
    if origin is not Annotated:
        return False

    return True


def _needs_injector(attr, ns=None):
    if isinstance(attr, type):
        return False

    if not callable(attr):
        return False

    if hasattr(attr, "injected_params"):
        return False

    return any(
        _is_at_annotation_type(annotation)
        for annotation in _get_annotations(attr, ns).values()
    )


inject = Dependency
