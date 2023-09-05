import pytest

from wordlette.cms.forms import Form, Field, ValidationError


def test_field_type_validation():
    class TestValueType(Field):
        def validate(self, value):
            if value == "invalid":
                raise ValidationError("Invalid value")

    class TestForm(Form):
        value: TestValueType

    with pytest.raises(ValidationError):
        TestForm("invalid")

    assert TestForm("valid").value == "valid"


def test_field_validation():
    class TestForm(Form):
        value: str

        def validate_value_is_not_invalid(self, value):
            if value == "invalid":
                raise ValidationError("Invalid value")

    with pytest.raises(ValidationError):
        TestForm("invalid")

    assert TestForm("valid").value == "valid"


def test_field_validation_by_type():
    class TestForm(Form):
        value: str

        def validate_type_str_is_not_invalid(self, value: str):
            if value == "invalid":
                raise ValidationError("Invalid value")

    with pytest.raises(ValidationError):
        TestForm("invalid")

    assert TestForm("valid").value == "valid"
