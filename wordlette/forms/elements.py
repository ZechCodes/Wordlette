from typing import Sequence, Any

from markupsafe import Markup


class Element:
    tag: str
    flag_attrs = frozenset(("required", "checked", "disabled", "selected"))

    def __init__(self, **attrs):
        self.attrs = self._clean_attrs(attrs)

    def __eq__(self, other):
        if not isinstance(other, Element):
            return False

        return self.tag == other.tag and self.attrs == other.attrs

    def __repr__(self):
        return f"<{type(self).__name__} {self.tag} {self.attrs}>"

    def render(self, **attr_overrides):
        return Markup(f"<{self.tag} {self._build_attrs(attr_overrides)} />")

    def _build_attrs(self, attr_overrides: dict[str, Any]) -> str:
        attrs_dict = self.attrs | self._clean_attrs(attr_overrides)
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
        if class_ := attrs.pop("class", None):
            attrs.setdefault("classes", []).extend(filter(bool, class_.split()))

        return attrs

    def _clean_attr_name(self, name: str) -> str:
        return name.replace("_", "-").rstrip("_").strip().casefold()


class ContainerElement(Element):
    def __init__(self, body: str | Element | Sequence[str | Element], **attrs):
        self.body = body
        super().__init__(**attrs)

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        return self.body == other.body

    def render(self, **kwargs):
        return Markup(
            f"<{self.tag} {self._build_attrs(kwargs)}>{Markup.escape(self.body)}</{self.tag}>"
        )


class AElement(ContainerElement):
    tag = "a"


class InputElement(Element):
    tag = "input"


class ButtonElement(ContainerElement):
    tag = "button"


class LabelElement(ContainerElement):
    tag = "label"
