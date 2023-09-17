import pytest

from wordlette.forms import Form, Field
from wordlette.forms.elements import ButtonElement, InputElement
from wordlette.forms.exceptions import FormValidationError
from wordlette.forms.field_types import (
    TextField,
    NumberField,
    SubmitButton,
    HiddenField,
)


def test_field_type_validation():
    class TestField(Field):
        def validate(self, value):
            if value == "invalid":
                raise FormValidationError("Invalid value", {}, Form())

    class TestForm(Form):
        value: int @ TestField

    with pytest.raises(FormValidationError):
        TestForm("invalid")

    assert TestForm("valid").value == "valid"


def test_field_validation():
    class TestForm(Form):
        value: str

        def validate_value_is_not_invalid(self, value):
            if value == "invalid":
                raise FormValidationError("Invalid value", {}, self)

    with pytest.raises(FormValidationError):
        TestForm("invalid")

    assert TestForm("valid").value == "valid"


def test_field_validation_by_type():
    class TestForm(Form):
        value: str

        def validate_type_str_is_not_invalid(self, value: str):
            if value == "invalid":
                raise FormValidationError("Invalid value", {}, self)

    with pytest.raises(FormValidationError):
        TestForm("invalid")

    assert TestForm("valid").value == "valid"


def test_too_large_ints():
    class TestForm(Form):
        value: int

    with pytest.raises(FormValidationError):
        TestForm(2**63)

    assert TestForm(2**63 - 1).value == 2**63 - 1


def test_too_small_ints():
    class TestForm(Form):
        value: int

    with pytest.raises(FormValidationError):
        TestForm(-(2**63) - 1)

    assert TestForm(-(2**63)).value == -(2**63)


def test_form_view_compose():
    class TestForm(Form):
        text_field: str @ TextField(
            name="text-field",
        )
        number_field: int @ NumberField(
            name="number-field",
            required=True,
        )
        field: int @ HiddenField() = 321

        buttons = (SubmitButton("Test"),)

    view = TestForm("Test", 123).view()
    elements = list(view.compose())

    assert elements == [
        InputElement(type="text", name="text-field", value="Test"),
        InputElement(type="number", name="number-field", value=123, required=True),
        InputElement(type="hidden", name="field", value=321),
        ButtonElement("Test", type="submit"),
    ]
