from typing import Sequence, Any

from markupsafe import Markup


class Element:
    tag: str
    flag_attrs = frozenset(("required", "checked", "disabled", "selected"))
    cloned: bool = False

    def __init__(self, **attrs):
        self.attrs = self._clean_attrs(attrs)

    def __eq__(self, other):
        if not isinstance(other, Element):
            return False

        return self.tag == other.tag and self.attrs == other.attrs

    def __repr__(self):
        return f"<{type(self).__name__} {self.tag} {self.attrs}>"


    def clone(self, **attrs) -> "Element":
        if self.cloned:
            self.attrs = attrs
            return self

        return self._create_clone(**attrs)

    def render(self):
        return Markup(f"<{self.tag} {self._build_attrs()} />")

    def _build_attrs(self) -> str:
        attrs_dict = self.attrs.copy()
        if classes := attrs_dict.pop("class", None):
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
        if isinstance(classes := attrs.get("class"), str):
            attrs["class"] = set(classes.split(" "))

        return attrs

    def _clean_attr_name(self, name: str) -> str:
        return name.rstrip("_").strip().replace("_", "-").casefold()

    def _create_clone(self, **attrs) -> "Element":
        clone = type(self)(**attrs)
        clone.cloned = True
        return clone


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


class AElement(ContainerElement):
    tag = "a"


class InputElement(Element):
    tag = "input"


class ButtonElement(ContainerElement):
    tag = "button"


class LabelElement(ContainerElement):
    tag = "label"
