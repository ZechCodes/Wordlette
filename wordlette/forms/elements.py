from typing import Sequence, Any

from markupsafe import Markup


class Element:
    tag: str
    has_closing_tag = False

    def __init__(self, **attrs):
        self.attrs = attrs

    def __eq__(self, other):
        if not isinstance(other, Element):
            return False

        return (
            self.tag == other.tag
            and self.attrs == other.attrs
            and self.has_closing_tag == other.has_closing_tag
        )

    def __repr__(self):
        return f"<{self.tag} {self.attrs}>"

    def render(self, **kwargs):
        return Markup(f"<{self.tag} {self._build_attrs(kwargs)} />")

    def _build_attrs(self, extra_attrs: dict[str, Any]) -> str:
        attrs = []
        attrs_dict = self._merge_attrs_dicts(self.attrs, extra_attrs)
        for name in ("required", "checked", "disabled", "selected"):
            if name in attrs_dict:
                attrs.append(name)
                del attrs_dict[name]

        attrs.extend(f'{k}="{Markup.escape(v)}"' for k, v in attrs_dict.items())
        return " ".join(attrs)

    def _merge_attrs_dicts(self, *args):
        attrs = {}
        for arg in args:
            for key, value in arg.items():
                clean_key = key.rstrip("_")
                if clean_key in attrs:
                    attrs[clean_key] += " " + value
                else:
                    attrs[clean_key] = value
        if class_ := attrs.pop("class", None):
            attrs.setdefault("classes", []).extend(filter(bool, class_.split()))

        return attrs


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
