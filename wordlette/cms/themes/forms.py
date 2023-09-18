from bevy import dependency, inject

from wordlette.cms.themes import ThemeManager
from wordlette.forms import Form as _Form


class Form(_Form):
    __form_template__: str = "form.html"

    @inject
    def render(
        self,
        __template: str | None = None,
        /,
        __tm: ThemeManager = dependency(),
        **context,
    ) -> str:
        template = __template or self.__form_template__
        return __tm.render_template(template, form=self, **context)
