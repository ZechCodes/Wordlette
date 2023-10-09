from typing import Sequence, Any, Iterable, Protocol, runtime_checkable
import re

from markupsafe import Markup


@runtime_checkable
class Renderable(Protocol):
    def render(self) -> Markup:
        ...


class Text(Renderable):
    def __init__(self, text: str):
        self.text = text

    def render(self) -> Markup:
        return Markup.escape(self.text)

    def __repr__(self):
        return f"<{type(self).__name__} {self.text!r}>"


class Element(Renderable):
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

    def render(self) -> Markup:
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

            case Element():
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

    def matches(self, element: Element) -> bool:
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


class ContainerElement(Element):
    def __init__(self, *body: str | Renderable | Sequence[str | Renderable], **attrs):
        self.body = tuple(self._process_nodes(body))
        super().__init__(**attrs)

    def append(self, *elements: str | Renderable) -> Self:
        self.body = (*self.body, *self._process_nodes(elements))
        return self

    def prepend(self, *elements: str | Renderable) -> Self:
        self.body = (*self._process_nodes(elements), *self.body)
        return self

    def insert_after(
        self, selector: str | Selector, *elements: str | Renderable
    ) -> Self:
        return self._insert_near(selector, 1, *elements)

    def insert_before(
        self, selector: str | Selector, *elements: str | Renderable
    ) -> Self:
        return self._insert_near(selector, 0, *elements)

    def _insert_near(
        self, selector: str | Selector, offset: int, *elements: str | Renderable
    ) -> Self:
        selector = Selector.factory(selector)
        for i, element in enumerate(self.body):
            if selector == element:
                self._insert_at(i + offset, *elements)
                break

        return self

    def _insert_at(self, index: int, *elements: str | Renderable) -> Self:
        self.body = (
            *self.body[:index],
            *self._process_nodes(elements),
            *self.body[index:],
        )
        return self

    def select(self, selector: str | Selector) -> Renderable | None:
        selector = Selector.factory(selector)
        for element in self.body:
            if selector == element:
                return element

        return None

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        return self.body == other.body

    def render(self) -> Markup:
        return Markup(
            f"<{self.tag} {self._build_attrs()}>{''.join(element.render() for element in self.body)}</{self.tag}>"
        )

    def _create_clone(self, **attrs) -> "ContainerElement":
        return type(self)(*self.body, __clone__=True, **attrs)

    def _process_nodes(
        self, nodes: Sequence[str | Element]
    ) -> Generator[Renderable, None, None]:
        for node in nodes:
            match node:
                case str():
                    yield Text(node)

                case Renderable():
                    yield node

                case _:
                    raise TypeError(f"Invalid body node type: {type(node)}")


class AElement(ContainerElement):
    tag = "a"


class InputElement(Element):
    tag = "input"


class ButtonElement(ContainerElement):
    tag = "button"


class LabelElement(ContainerElement):
    tag = "label"


class OptionElement(ContainerElement):
    tag = "option"


class SelectElement(ContainerElement):
    tag = "select"

    def __init__(self, *body, placeholder: str | None = None, **kwargs):
        if placeholder:
            body = (
                OptionElement(
                    placeholder, disabled=True, selected=True, value="--default--"
                ),
                *body,
            )
            kwargs.setdefault("value", "--default--")

        super().__init__(*body, **kwargs)

    def render(self) -> Markup:
        return Markup(
            f"<{self.tag} {self._build_attrs()}>"
            f"{''.join(map(OptionElement.render, self.body))}"
            f"</{self.tag}>"
        )
