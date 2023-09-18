from typing import Sequence


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


class ContainerElement(Element):
    has_closing_tag = True

    def __init__(self, body: str | Element | Sequence[str | Element], **attrs):
        self.body = body
        super().__init__(**attrs)

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        return self.body == other.body


class AElement(ContainerElement):
    tag = "a"


class InputElement(Element):
    tag = "input"


class ButtonElement(ContainerElement):
    tag = "button"


class LabelElement(ContainerElement):
    tag = "label"
