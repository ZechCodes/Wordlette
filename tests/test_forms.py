import pytest

from wordlette.forms import Form, Field
from wordlette.forms.exceptions import FormValidationError


def test_field_type_validation():
    class TestValueType(Field):
        def validate(self, value):
            if value == "invalid":
                raise FormValidationError("Invalid value", {}, Form())

    class TestForm(Form):
        value: TestValueType

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
