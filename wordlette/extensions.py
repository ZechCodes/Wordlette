from dataclasses import dataclass
from importlib import import_module
from pathlib import Path


@dataclass
class Extension:
    name: str
    import_path: str

    def load_extension(self):
        return import_module(self.import_path)

    def __iter__(self):
        yield from (self.name, self)


def scan_directory_for_public_modules(directory: Path) -> set[Path]:
    return {
        path
        for path in directory.iterdir()
        if (
            not path.name.startswith("_")
            and (path.suffix in {".py", ".pyc"} or path.is_dir())
        )
    }


def get_extensions_in_directory(directory: Path) -> list[Extension]:
    return [
        Extension(path.stem, f"{path.parent.name}.{path.stem}")
        for path in scan_directory_for_public_modules(directory)
    ]
