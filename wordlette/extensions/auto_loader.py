from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Generator, Iterable, TypeVar

from wordlette.extensions.loader import load_extension_package

T = TypeVar("T", bound=type)


@dataclass()
class ExtensionInfo:
    path: Path
    import_path: str
    module: ModuleType
    found_classes: dict[T, set[T]]


def auto_load_directory(
    path: Path, scan_for: Iterable[T]
) -> Generator[None, tuple[Path, ExtensionInfo], None]:
    for file in path.iterdir():
        if can_import(file):
            yield file, import_package_from_file(file, path.stem, scan_for)


def can_import(path: Path) -> bool:
    if path.name.startswith("_"):
        return False

    return is_python_file(path) or is_package(path)


def import_package_from_file(
    path: Path, package: str, scan_for: Iterable[T]
) -> ExtensionInfo:
    import_path = f"{package}.{path.stem}"
    return import_package(path, import_path, package, scan_for)


def import_package(
    path: Path, import_path: str, package: str, scan_for: Iterable[T]
) -> ExtensionInfo:
    module, found_classes = load_extension_package(import_path, scan_for, package)
    return ExtensionInfo(path, import_path, module, found_classes)


def is_package(path: Path) -> bool:
    return (path / "__init__.py").exists()


def is_python_file(path: Path) -> bool:
    return path.suffix in {".py", ".pyc"}
