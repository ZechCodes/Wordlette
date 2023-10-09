from markupsafe import Markup

from wordlette.core.html.renderables import Renderable


class Text(Renderable):
    def __init__(self, text: str):
        self.text = text

    def render(self) -> Markup:
        return Markup.escape(self.text)

    def __repr__(self):
        return f"<{type(self).__name__} {self.text!r}>"
