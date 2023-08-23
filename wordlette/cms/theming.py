import logging
from pathlib import Path
from typing import Annotated, Any, Mapping

import jinja2
from bevy import inject, dependency
from starlette.background import BackgroundTask
from starlette.responses import HTMLResponse, Response

from wordlette.cms.exceptions import ThemeNotFound, TemplateNotFound
from wordlette.utils.options import Option, Value, Null

logger = logging.getLogger("Theming")


class ThemeManager:
    wordlette_res: Annotated[Path, "package-resources"] = dependency()

    def __init__(self):
        self._theme = None
        self._secondary_themes = []
        self._jinja = jinja2.Environment(loader=JinjaTemplateLoader(self))

    @property
    def default_theme(self) -> Path:
        return self.wordlette_res / "themes" / "default"

    def find_template(self, template_name: str) -> Option[Path]:
        for theme in self._iterate_themes():
            template_location = theme / template_name
            if template_location.exists():
                return Value(template_location)

        return Null(
            TemplateNotFound(
                f"Could not find a template named {template_name!r} in any of the active themes."
            )
        )

    def set_theme(self, theme_location: Path):
        if not theme_location.exists():
            raise ThemeNotFound(
                f"Could not find a theme at {theme_location.resolve()}."
            )

        self._theme = theme_location
        logger.debug(f"Set theme to {theme_location.resolve()}")

    def add_secondary_theme(self, theme_location: Path):
        if not theme_location.exists():
            raise ThemeNotFound(
                f"Could not find a theme at {theme_location.resolve()} to use as a secondary theme."
            )

        self._secondary_themes.append(theme_location)

    def render_template(self, template_name: str, **context: Any) -> str:
        return self._jinja.get_template(template_name).render(**context)

    def _iterate_themes(self):
        if self._theme:
            yield self._theme

        yield from self._secondary_themes
        yield self.default_theme


class JinjaTemplateLoader(jinja2.BaseLoader):
    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager

    def get_source(self, environment, template):
        match self.theme_manager.find_template(template):
            case Value(template_location):
                return self._load_template(template_location)

            case Null(exception):
                raise exception

    def _load_template(self, template_location: Path):
        logger.debug(
            f"Found template {template_location.name!r} at {template_location.resolve()}"
        )

        last_mtime = template_location.stat().st_mtime

        def is_current():
            return template_location.stat().st_mtime == last_mtime

        with template_location.open() as template_file:
            return template_file.read(), str(template_location), is_current


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
