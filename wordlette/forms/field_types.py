import re
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Annotated

from wordlette.forms import Field
from wordlette.forms.elements import ButtonElement, AElement
from wordlette.forms.fields import NotSet, not_set


class Week:
    def __init__(self, year: int, week: int):
        if week < 1 or week > 52:
            raise ValueError("Week must be between 1 and 52")

        self.year = year
        self.week = week


class CaptureType(str, Enum):
    USER = "user"
    ENVIRONMENT = "environment"


class FormEncodingType(str, Enum):
    APPLICATION_X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"


class Label:
    def __init__(self, text: str, for_: str = ""):
        self.text = text
        self.for_ = for_


class InputField(Field):
    type: str

    def __init__(
        self,
        *,
        disabled: bool | NotSet = not_set,
        value: Any | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(
            **self._filter_and_clean_params(
                type_=self.type,
                disabled=disabled,
                value=value,
                **kwargs,
            )
        )


class TextField(InputField):
    type = "text"

    def __init__(
        self,
        *,
        max_length: int | NotSet = not_set,
        min_length: int | NotSet = not_set,
        pattern: str | NotSet = not_set,
        placeholder: str | NotSet = not_set,
        readonly: bool | NotSet = not_set,
        size: int | NotSet = not_set,
        spellcheck: bool | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(
            maxlength=max_length,
            minlength=min_length,
            pattern=pattern,
            placeholder=placeholder,
            readonly=readonly,
            size=size,
            spellcheck=spellcheck,
            **kwargs,
        )


class ButtonField(InputField):
    type = "button"


class CheckBoxField(InputField):
    type = "checkbox"

    def __init__(self, checked: bool | NotSet = not_set, **kwargs):
        super().__init__(checked=checked, **kwargs)

    @property
    def required(self):
        return False

    def convert_to_bool(self, value: str) -> bool:
        if "value" in self.attrs:
            return value == self.attrs["value"]

        return value.casefold() == "on"


class ColorField(InputField):
    type = "color"

    def __init__(self, value: str | NotSet = not_set, **kwargs):
        if value is not not_set and not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValueError("Color value must be a valid hex color code")

        super().__init__(value=value, **kwargs)


class DateField(InputField):
    type = "date"

    def __init__(
        self,
        *,
        min_date: date | NotSet = not_set,
        max_date: date | NotSet = not_set,
        step: Annotated[int | NotSet, "A step set in days"] = not_set,
        **kwargs,
    ):
        super().__init__(min=min_date, max=max_date, step=step, **kwargs)


class DateTimeField(InputField):
    type = "datetime-local"

    def __init__(
        self,
        *,
        min_datetime: datetime | NotSet = not_set,
        max_datetime: datetime | NotSet = not_set,
        step: timedelta | NotSet = not_set,
        value: datetime | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(
            max=max_datetime,
            min=min_datetime,
            step=step,
            value=value,
            **kwargs,
        )


class EmailField(TextField):
    type = "email"

    def __init__(self, *, pattern: str | NotSet = not_set, **kwargs):
        super().__init__(pattern=pattern, **kwargs)


class MultipleEmailField(EmailField):
    def __init__(self, *, pattern: str | NotSet = not_set, **kwargs):
        super().__init__(pattern=pattern, **kwargs)


class FileField(InputField):
    type = "file"

    def __init__(
        self,
        *,
        accept: str | NotSet = not_set,
        capture: CaptureType | str | NotSet = not_set,
        **kwargs,
    ):
        if "value" in kwargs:
            raise ValueError("You cannot set the value of a file field")

        super().__init__(
            accept=accept,
            capture=capture,
            **kwargs,
        )


class MultipleFileField(FileField):
    def __init__(
        self,
        *,
        accept: str | NotSet = not_set,
        capture: CaptureType | str | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(accept=accept, capture=capture, **kwargs)


class HiddenField(InputField):
    type = "hidden"


class MonthField(InputField):
    type = "month"

    def __init__(
        self,
        *,
        min_month: date | NotSet = not_set,
        max_month: date | NotSet = not_set,
        step: Annotated[int | NotSet, "A step set in months"] = not_set,
        **kwargs,
    ):
        super().__init__(max=max_month, min=min_month, step=step, **kwargs)


class NumberField(InputField):
    type = "number"

    def __init__(
        self,
        min_value: int | NotSet = not_set,
        max_value: int | NotSet = not_set,
        step: int | NotSet = not_set,
        value: int | NotSet = not_set,
        **kwargs,
    ):
        self._validate(min_value, max_value, step, value)
        super().__init__(max=max_value, min=min_value, step=step, value=value, **kwargs)

    def _validate(self, min_value, max_value, step, value):
        if step is not not_set and step <= 0:
            raise ValueError("step must be greater than 0")

        if (
            min_value is not not_set
            and max_value is not not_set
            and min_value >= max_value
        ):
            raise ValueError("min_value must be less than max_value")

        if min_value is not not_set and not isinstance(min_value, (int, Decimal)):
            raise TypeError("min_value must be an integer or Decimal")

        if max_value is not not_set and not isinstance(max_value, (int, Decimal)):
            raise TypeError("max_value must be an integer or Decimal")

        if value is not not_set and not isinstance(value, (int, Decimal)):
            raise TypeError("value must be an integer or Decimal")


class PasswordField(TextField):
    type = "password"


class RadioButtonField(InputField):
    type = "radio"

    def __init__(self, *, value: Any, checked: bool | NotSet = not_set, **kwargs):
        super().__init__(value=value, checked=checked, **kwargs)

    def convert_to_bool(self, value: str) -> bool:
        return value == self.value


class RangeField(InputField):
    type = "range"

    def __init__(
        self,
        *,
        min_value: int | NotSet = not_set,
        max_value: int | NotSet = not_set,
        step: int | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(max=max_value, min=min_value, step=step, **kwargs)


class SearchField(TextField):
    type = "search"


class SubmitField(InputField):
    type = "submit"

    def __init__(
        self,
        *,
        form_action: Annotated[
            str | NotSet, "Populates the HTML formaction attribute"
        ] = not_set,
        form_encoding: Annotated[
            FormEncodingType | NotSet, "Populates the HTML formenctype attribute"
        ] = not_set,
        form_method: Annotated[
            str | NotSet, "Populates the HTML formmethod attribute"
        ] = not_set,
        form_no_validate: Annotated[
            bool | NotSet, "Populates the HTML formnovalidate attribute"
        ] = not_set,
        form_target: Annotated[
            str | NotSet, "Populates the HTML formtarget attribute"
        ] = not_set,
        **kwargs,
    ):
        super().__init__(
            formaction=form_action,
            formenctype=form_encoding,
            formmethod=form_method,
            formnovalidate=form_no_validate,
            formtarget=form_target,
            **kwargs,
        )


class ImageField(SubmitField):
    type = "image"

    def __init__(
        self,
        *,
        alt: str | NotSet = not_set,
        height: int | NotSet = not_set,
        width: int | NotSet = not_set,
        src: str | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(alt=alt, height=height, width=width, src=src, **kwargs)


class TelField(TextField):
    type = "tel"


class TimeField(InputField):
    type = "time"

    def __init__(
        self,
        *,
        min_time: time | NotSet = not_set,
        max_time: time | NotSet = not_set,
        step: timedelta | NotSet = not_set,
        value: time | NotSet = not_set,
        readonly: bool | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(
            max=max_time,
            min=min_time,
            step=step,
            value=value,
            readonly=readonly,
            **kwargs,
        )


class UrlField(TextField):
    type = "url"


class WeekField(InputField):
    type = "week"

    def __init__(
        self,
        *,
        min_week: Week | NotSet = not_set,
        max_week: Week | NotSet = not_set,
        step: Annotated[int | NotSet, "A step set in weeks"] = not_set,
        readonly: bool | NotSet = not_set,
        **kwargs,
    ):
        super().__init__(
            max=max_week, min=min_week, step=step, readonly=readonly, **kwargs
        )


class Button:
    button_type: str = "button"

    def __init__(self, text: str, **attrs):
        self.text = text
        self.attrs = attrs | {"type": self.button_type}

    def compose(self):
        return ButtonElement(self.text, **self.attrs)


class SubmitButton(Button):
    button_type = "submit"


class ResetButton(Button):
    button_type = "reset"


class Link:
    def __init__(self, text: str, href: str | NotSet = not_set, **attrs):
        self.attrs = {key.rstrip("_"): value for key, value in attrs.items()}
        self.text = text

        if href is not not_set:
            self.attrs["href"] = href

    def compose(self):
        return AElement(self.text, **self.attrs)
