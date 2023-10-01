from importlib import import_module
from pathlib import Path


class Extension:
    __match_args__ = ("name",)

    name: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            cls.name = cls.__name__

    def __iter__(self):
        yield from (self.name, self)

    def __repr__(self):
        return f"<Extension:{self.name}>"


class PackageExtension(Extension):
    __slots__ = ("name", "package_import")

    def __init__(self, name: str, package_import: str):
        self.name = name
        self.package_import = package_import

    def load_extension(self):
        return import_module(self.package_import)


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
        PackageExtension(path.stem, f"{path.parent.name}.{path.stem}")
        for path in scan_directory_for_public_modules(directory)
    ]
