from bevy import dependency, inject
from markupsafe import Markup

from wordlette.cms.themes import ThemeManager
from wordlette.forms import Form as _Form
from wordlette.forms.views import FormView as _FormView
from wordlette.utils.contextual_methods import contextual_method


class FormView(_FormView):
    def __init__(self, template: str, *args):
        super().__init__(*args)
        self.template = template

    @inject
    def render(
        self,
        __template: str | None = None,
        /,
        __tm: ThemeManager = dependency(),
        **context,
    ) -> str:
        template = __template or self.template
        return Markup(__tm.render_template(template, form=self, **context))


class Form(_Form):
    __form_template__: str = "form.html"
    __form_view_type__ = FormView

    @contextual_method
    def render(self):
        return self.view().render()

    @contextual_method
    def view(self) -> FormView:
        return self.__form_view_type__(
            self.__form_template__,
            self.__form_fields__,
            self.buttons,
            self.__field_values__,
            self._validate_fields(),
        )

    @view.classmethod
    def view(cls) -> FormView:
        return cls.__form_view_type__(
            cls.__form_template__,
            cls.__form_fields__,
            cls.buttons,
            {},
            {},
        )
