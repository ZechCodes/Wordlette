from pathlib import Path

import jinja2

import wordlette.cms.themes.theme_managers as tm
from wordlette.utils.options import Value, Null


class JinjaTemplateLoader(jinja2.BaseLoader):
    def __init__(self, theme_manager: "tm.ThemeManager"):
        self.theme_manager = theme_manager

    def get_source(self, environment, template):
        match self.theme_manager.find_template(template):
            case Value(template_location):
                return self._load_template(template_location)

            case Null(exception):
                raise exception

    def _load_template(self, template_location: Path):
        tm.logger.debug(
            f"Found template {template_location.name!r} in {template_location.parent.resolve()}"
        )

        last_mtime = template_location.stat().st_mtime

        def is_current():
            return template_location.stat().st_mtime == last_mtime

        with template_location.open() as template_file:
            return template_file.read(), str(template_location), is_current
