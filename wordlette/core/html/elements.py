from markupsafe import Markup

from wordlette.core.html.base_elements import Element, ContainerElement


class Link(ContainerElement):
    tag = "a"


class Div(ContainerElement):
    tag = "div"


class Input(Element):
    tag = "input"


class Checkbox(Input):
    def __init__(
        self,
        *,
        checked: bool = False,
        label: str | None = None,
        name: str | None = None,
        value: str | None,
        **attrs,
    ):
        self.label = label

        attrs["checked"] = checked

        if name:
            attrs["name"] = name

        if value:
            attrs["value"] = value

        attrs.setdefault("type", "checkbox")

        super().__init__(**attrs)

    def render(self) -> Markup:
        return Markup(f"<input {self._build_attrs()} />")


class RadioButton(Checkbox):
    def __init__(
        self,
        *,
        checked: bool = False,
        name: str | None = None,
        value: str | None,
        label: str | None = None,
        **attrs,
    ):
        super().__init__(
            type="radio", checked=checked, label=label, name=name, value=value, **attrs
        )


class Button(ContainerElement):
    tag = "button"


class Label(ContainerElement):
    tag = "label"


class Option(ContainerElement):
    tag = "option"


class Select(ContainerElement):
    tag = "select"

    def __init__(self, *body, placeholder: str | None = None, **kwargs):
        if placeholder:
            body = (
                Option(
                    placeholder, disabled=True, selected=True, value="--default--"
                ),
                *body,
            )
            kwargs.setdefault("value", "--default--")

        super().__init__(*body, **kwargs)

    def render(self) -> Markup:
        return Markup(
            f"<{self.tag} {self._build_attrs()}>"
            f"{''.join(map(Option.render, self.body))}"
            f"</{self.tag}>"
        )


class Legend(ContainerElement):
    tag = "legend"


class Fieldset(ContainerElement):
    tag = "fieldset"

    def __init__(self, *body, legend: str | None = None, **kwargs):
        super().__init__(*body, **kwargs)
        if legend:
            self.prepend(Legend(legend))

    def render(self):
        return Markup(
            f"<{self.tag} {self._build_attrs()}>"
            f"{''.join(elem.render() for elem in self.body)}"
            f"</{self.tag}>"
        )
