import re

import wordlette.core.html.elements as elements


class Selector:
    def __init__(
        self,
        tag: str | None = None,
        id_: str | None = None,
        classes: set[str] | None = None,
    ):
        self.tag = tag
        self.id = id_
        self.classes = classes or set()

    def __eq__(self, other):
        match other:
            case Selector():
                return (
                    self.tag == other.tag
                    and self.id == other.id
                    and self.classes == other.classes
                )

            case elements.Element():
                return self.matches(other)

            case _:
                return super().__eq__(other)

    def __repr__(self):
        return f"{type(self).__name__}({self.tag!r}, {self.id!r}, {self.classes!r})"

    def __str__(self):
        string_parts = []
        if self.tag:
            string_parts.append(self.tag)

        if self.id:
            string_parts.append(f"#{self.id}")

        if self.classes:
            string_parts.extend(f".{class_}" for class_ in self.classes)

        return "".join(string_parts)

    def matches(self, element: "elements.Element") -> bool:
        if self.tag and self.tag != element.tag:
            return False

        if self.id and self.id != element.attrs.get("id"):
            return False

        if self.classes and self.classes - element.classes:
            return False

        return True

    @classmethod
    def factory(cls, selector: "str | Selector") -> "Selector":
        match selector:
            case Selector():
                return selector
            case str():
                return cls.from_string(selector)
            case _:
                raise TypeError(f"Invalid selector: {selector!r}")

    @classmethod
    def from_string(cls, selector: str) -> "Selector":
        tag, id_, classes = cls._parse_selector(selector)
        return cls(tag, id_, classes)

    @classmethod
    def _parse_selector(cls, selector: str) -> tuple[str | None, str | None, set[str]]:
        match = re.match(
            r"^([a-z0-9\-_]+)?(#[a-z0-9-_]+)?((?:\.[a-z0-9-_]+)+)?$",
            selector,
            re.IGNORECASE,
        )
        if not match:
            return None, None, set()

        tag, id_, classes = match.groups()
        if id_:
            id_ = id_[1:]

        if classes:
            classes = set(filter(bool, classes[1:].split(".")))

        return tag, id_, classes
