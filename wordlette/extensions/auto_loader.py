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
            yield file, import_package_from_file(file, scan_for, path.stem)


def can_import(path: Path) -> bool:
    if path.name.startswith("_"):
        return False

    return is_python_file(path) or is_package(path)


def import_package_from_file(
    path: Path, scan_for: Iterable[T], package: str
) -> ExtensionInfo:
    import_path = f"{package}.{path.stem}"
    return import_package(import_path, scan_for, package, path)


def import_package(
    import_path: str,
    scan_for: Iterable[T] = (),
    package: str = "",
    path: Path | None = None,
) -> ExtensionInfo:
    module, found_classes = load_extension_package(import_path, scan_for, package)
    module_path = path or Path(module.__file__)
    return ExtensionInfo(module_path, import_path, module, found_classes)


def is_package(path: Path) -> bool:
    return (path / "__init__.py").exists()


def is_python_file(path: Path) -> bool:
    return path.suffix in {".py", ".pyc"}
