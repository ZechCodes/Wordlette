import logging
from pathlib import Path
from typing import Annotated, Any

import jinja2
from bevy import dependency

from wordlette.cms.exceptions import TemplateNotFound, ThemeNotFound
from wordlette.cms.themes.template_loaders import JinjaTemplateLoader
from wordlette.utils.options import Option, Value, Null

logger = logging.getLogger("Theming")


class ThemeManager:
    wordlette_res: Annotated[Path, "package-resources"] = dependency()

    def __init__(self):
        self._theme = None
        self._secondary_themes = []
        self._jinja = jinja2.Environment(
            loader=JinjaTemplateLoader(self), autoescape=True
        )

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
                f"Could not find a template with the name {template_name!r} in any of the active themes."
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
