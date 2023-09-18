from typing import Any, Mapping

from bevy import inject, dependency
from starlette.background import BackgroundTask
from starlette.responses import HTMLResponse, Response

from wordlette.cms.themes.theme_managers import ThemeManager


class Template(Response):
    def __init__(
        self,
        _template_name: str,
        _status_code: int = 200,
        *,
        _headers: Mapping[str, str] | None = None,
        _media_type: str | None = None,
        _background: BackgroundTask | None = None,
        **context: Any,
    ):
        self.name = _template_name
        self.context = context
        self.status_code = _status_code
        self._headers = _headers
        self.media_type = _media_type
        self.background = _background

    def __call__(self, *args, **kwargs):
        return HTMLResponse(
            self._render(),
            self.status_code,
            self.headers,
            self.media_type,
            self.background,
        )(*args, **kwargs)

    @inject
    def _render(self, theme_manager: ThemeManager = dependency()) -> str:
        return theme_manager.render_template(self.name, **self.context)
