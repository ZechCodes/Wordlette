import pytest

from wordlette.core.forms import Form, Field
from wordlette.core.forms import FormValidationError
from wordlette.core.forms.field_types import (
    TextField,
    NumberField,
    SubmitButton,
    HiddenField,
    CheckBoxField,
)
from wordlette.core.html.elements import Button, Input


def test_field_type_validation():
    class TestField(Field):
        def validate(self, value):
            if value == "invalid":
                raise FormValidationError("Invalid value", {}, Form())

    class TestForm(Form):
        value: str @ TestField

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

        buttons = SubmitButton("Test")

    view = TestForm.view()
    elements = [*view.fields.values(), *view.buttons]

    assert elements == [
        Input(type="text", name="text-field"),
        Input(type="number", name="number-field", required=True),
        Input(type="hidden", name="field", value=321),
        Button("Test", type="submit"),
    ]


def test_form_view_compose_with_values():
    class TestForm(Form):
        text_field: str @ TextField(
            name="text-field",
        )
        number_field: int @ NumberField(
            name="number-field",
            required=True,
        )
        field: int @ HiddenField() = 321

        buttons = SubmitButton("Test")

    view = TestForm("Test", 123).view()
    elements = [*view.fields.values(), *view.buttons]

    assert elements == [
        Input(type="text", name="text-field", value="Test"),
        Input(type="number", name="number-field", value=123, required=True),
        Input(type="hidden", name="field", value=321),
        Button("Test", type="submit"),
    ]


def test_form_field_converters():
    class TestForm(Form):
        field_a: bool @ TextField()
        field_b: int @ NumberField()
        field_c: float @ NumberField()

    form = TestForm("Field A", "20", "0.2")
    assert form.field_a is True
    assert form.field_b == 20
    assert form.field_c == 0.2


def test_form_checkbox_convert():
    class TestForm(Form):
        box_a: bool @ CheckBoxField(
            name="box-a",
        )
        box_b: bool @ CheckBoxField(
            name="box-b",
            value="Box B",
        )
        box_c: str @ CheckBoxField(
            name="box-c",
            value="Box C",
        )

    form = TestForm("on", "Box B", "Box C")
    assert form.box_a is True
    assert form.box_b is True
    assert form.box_c == "Box C"

    form = TestForm("off", "off", "off")
    assert form.box_a is False
    assert form.box_b is False
    assert form.box_c is "off"


def test_field_default_values():
    class TestForm(Form):
        field_a: str | None @ TextField(
            value="value a",
        )
        field_b: str @ TextField(
            default="default b",
        )
        field_c: str @ TextField() = "default & value c"
        field_d: str | None @ TextField()

    form = TestForm()
    fields = form.__form_fields__
    assert form.field_a is None
    assert fields["field_a"].attrs["value"] == "value a"

    assert form.field_b == "default b"
    assert "value" not in fields["field_b"].attrs

    assert form.field_c == "default & value c"
    assert fields["field_c"].attrs["value"] == "default & value c"

    assert form.field_d is None
    assert "value" not in fields["field_d"].attrs


def test_optional_annotations():
    class TestForm(Form):
        field_a: str | None @ TextField()
        field_b: str @ TextField()
        field_c: str @ CheckBoxField()

    assert TestForm.__form_fields__["field_a"].required is False
    assert TestForm.__form_fields__["field_b"].required is True
    assert TestForm.__form_fields__["field_c"].required is False
