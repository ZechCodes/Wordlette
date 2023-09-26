from typing import Any

from wordlette.cms.forms import Form


class DatabaseSettingsForm(Form):
    def convert_to_dict(self) -> dict[str, Any]:
        data = {}
        for name in self.__form_field_names__:
            data[name] = self.get_field_value(name)

        return data
