from importlib import import_module
from typing import Generator, Iterable, TypeVar
from types import ModuleType


T = TypeVar("T", bound=type)


def load_extension_package(
    package_import_path: str,
    scan_for: Iterable[T] = tuple(),
    package: str | None = None,
) -> tuple[ModuleType, dict[T, set[T]]]:
    return (
        import_module(package_import_path, package),
        _get_all_subclasses_in_package(scan_for, package_import_path),
    )


def _get_all_subclasses_in_package(
    scan_for: Iterable[T], search_package: str
) -> dict[T, set[T]]:
    return {
        scan_type: set(_get_subclasses_in_package(scan_type, search_package))
        for scan_type in scan_for
    }


def _get_subclasses_in_package(
    base_class: T, search_package: str
) -> Generator[None, T, None]:
    for subclass in base_class.__subclasses__():
        if subclass.__module__.startswith(search_package):
            yield subclass
            yield from _get_subclasses_in_package(subclass, search_package)
