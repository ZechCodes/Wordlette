from typing import Sequence, Any, Iterable

from markupsafe import Markup


class Element:
    tag: str
    flag_attrs = frozenset(("required", "checked", "disabled", "selected"))

    def __init__(self, *, __clone__: bool = False, **attrs):
        self.attrs = self._clean_attrs(attrs)
        self.cloned = __clone__

    def __eq__(self, other):
        if not isinstance(other, Element):
            return False

        return self.tag == other.tag and self.attrs == other.attrs

    def __repr__(self):
        return f"<{type(self).__name__} {self.tag} {self.attrs}>"

    @property
    def classes(self) -> set[str]:
        return self.attrs.get("class", set())

    def add_attr(self, **new_attrs: Any) -> "Element":
        return self.clone(**self.attrs | new_attrs)

    def add_class(self, *new_classes: str) -> "Element":
        return self.clone(**self.attrs | {"class": self.classes | set(new_classes)})

    def clone(self, **attrs) -> "Element":
        if self.cloned:
            self.attrs = attrs
            return self

        return self._create_clone(**attrs)

    def remove(self, *remove_attrs: str) -> "Element":
        return self.clone(
            **{k: v for k, v in self.attrs.items() if k not in remove_attrs}
        )

    def render(self):
        return Markup(f"<{self.tag} {self._build_attrs()} />")

    def _build_attrs(self) -> str:
        attrs_dict = self.attrs.copy()
        classes = self._process_classes(attrs_dict.pop("class", set()))
        classes |= self._process_classes(attrs_dict.pop("classes", set()))
        if classes:
            attrs_dict["class"] = " ".join(classes)

        attrs = [
            f'{k}="{Markup.escape(v)}"'
            for k, v in attrs_dict.items()
            if k not in self.flag_attrs
        ]
        flags = [
            name for name in self.flag_attrs if attrs_dict.get(name, False) is not False
        ]
        return " ".join(attrs + flags)

    def _clean_attrs(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = {self._clean_attr_name(k): v for k, v in attrs.items()}
        classes = self._process_classes(attrs.pop("classes", set()))
        classes |= self._process_classes(attrs.pop("class", set()))
        if classes:
            attrs["class"] = classes

        return attrs

    def _clean_attr_name(self, name: str) -> str:
        return name.rstrip("_").strip().replace("_", "-").casefold()

    def _create_clone(self, **attrs) -> "Element":
        return type(self)(__clone__=True, **attrs)

    def _process_classes(self, classes: str | Iterable[str]) -> set[str]:
        match classes:
            case str():
                return set(classes.split())

            case _:
                return set(classes)


class ContainerElement(Element):
    def __init__(self, body: str | Element | Sequence[str | Element], **attrs):
        self.body = body
        super().__init__(**attrs)

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        return self.body == other.body

    def render(self):
        return Markup(
            f"<{self.tag} {self._build_attrs()}>{Markup.escape(self.body)}</{self.tag}>"
        )

    def _create_clone(self, **attrs) -> "ContainerElement":
        return type(self)(self.body, __clone__=True, **attrs)


class AElement(ContainerElement):
    tag = "a"


class InputElement(Element):
    tag = "input"


class ButtonElement(ContainerElement):
    tag = "button"


class LabelElement(ContainerElement):
    tag = "label"
