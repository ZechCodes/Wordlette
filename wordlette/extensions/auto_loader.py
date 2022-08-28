from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Generator, Iterable, TypeVar

from wordlette.extensions.loader import load_extension_package

T = TypeVar("T", bound=type)


@dataclass()
class ExtensionInfo:
    import_path: str
    module: ModuleType
    found_classes: dict[T, set[T]]


def auto_load_directory(
    path: Path, scan_for: Iterable[T]
) -> Generator[None, tuple[Path, ExtensionInfo], None]:
    package = path.stem
    for file in path.iterdir():
        if can_import(file):
            import_path = f"{package}.{file.stem}"
            module, found_classes = load_extension_package(
                import_path, scan_for, package
            )
            info = ExtensionInfo(import_path, module, found_classes)
            yield file, info


def can_import(path: Path) -> bool:
    return is_python_file(path) or is_package(path)


def is_python_file(path: Path) -> bool:
    return path.suffix in {".py", ".pyc"}


def is_package(path: Path) -> bool:
    return (path / "__init__.py").exists()
