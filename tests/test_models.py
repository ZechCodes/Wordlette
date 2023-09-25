from datetime import datetime, date, time
from itertools import count
from typing import Annotated

import pytest

from wordlette.models import FieldSchema, Model, ValidationError
from wordlette.models.auto import Auto


def test_model_schemas():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema()

    assert TestModel.id.name == "id"
    assert TestModel.id.type is int

    assert TestModel.name.name == "name"
    assert TestModel.name.type is str


def test_model_optional_fields():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str | None @ FieldSchema()

    model = TestModel(id=1)
    assert model.id == 1
    assert model.name is None


def test_model_init():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema()

    model = TestModel(id=1, name="test")
    assert model.id == 1
    assert model.name == "test"


def test_model_init_with_defaults():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema() = "test"

    model = TestModel(id=1)
    assert model.id == 1
    assert model.name == "test"


def test_model_init_with_defaults_and_override():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema() = "test"

    model = TestModel(id=1, name="test2")
    assert model.id == 1
    assert model.name == "test2"


def test_model_init_with_missing_required():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema()

    with pytest.raises(TypeError):
        TestModel()


def test_model_init_incompatible_types():
    class TestModel(Model):
        id: int @ FieldSchema()

    model = TestModel(id="test")
    assert isinstance(model.__validation_errors__["id"], ValueError)


def test_loud_model_init_incompatible_types():
    class TestModel(Model):
        id: int @ FieldSchema()

    with pytest.raises(ValidationError):
        TestModel.raise_on_error(id="test")


def test_model_to_dict():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema()

    class TestParentModel(Model):
        child: TestModel @ FieldSchema()

    model = TestParentModel(child=TestModel(id=1, name="test"))
    assert model.to_dict() == {"child": {"id": 1, "name": "test"}}


def test_sequence_type_conversion():
    class TestModel(Model):
        values: list[int] @ FieldSchema()

    model = TestModel(values=range(1, 4))
    assert model.values == [1, 2, 3]


def test_annotated_hints():
    class TestModel(Model):
        id: Annotated[int, FieldSchema()]
        name: Annotated[str, FieldSchema()]

    class TestParentModel(Model):
        child: Annotated[TestModel, FieldSchema()]

    model = TestParentModel(child=TestModel(id=1, name="test"))
    assert model.to_dict() == {"child": {"id": 1, "name": "test"}}


def test_inherited_models():
    class TestModel(Model):
        id: int @ FieldSchema
        name: str @ FieldSchema

    class TestChildModel(TestModel):
        age: int @ FieldSchema

    model = TestChildModel(id=1, name="test", age=30)
    assert model.to_dict() == {"id": 1, "name": "test", "age": 30}


def test_joined_models():
    class TestModelA(Model):
        id: int @ FieldSchema
        name: str @ FieldSchema

    class TestModelB(Model):
        age: int @ FieldSchema

    data = {"id": 1, "name": "test", "age": 30}
    JoinedModel = TestModelA & TestModelB

    model = TestModelA(**data)
    assert model.to_dict() == {"id": 1, "name": "test"}

    model = TestModelB(**data)
    assert model.to_dict() == {"age": 30}

    model = JoinedModel(**data)
    assert model.to_dict() == data


def test_auto_fields():
    counter = count()

    class TestModel(Model):
        __auto_field_factories__ = {int: lambda *_: next(counter)}
        id: int | Auto @ FieldSchema

    models = (TestModel(), TestModel(), TestModel())
    assert tuple(model.id for model in models) == (0, 1, 2)


def test_auto_fields_types():
    class TestModel(Model):
        datetime_field: datetime | Auto @ FieldSchema
        date_field: date | Auto @ FieldSchema
        time_field: time | Auto @ FieldSchema
        int_field: int | Auto @ FieldSchema
        float_field: float | Auto @ FieldSchema
        str_field: str | Auto @ FieldSchema

    models = (TestModel(), TestModel(), TestModel())
    types = [field.type for field in TestModel.__fields__.values()]
    assert all(
        isinstance(value, type_)
        for model in models
        for value, type_ in zip(model.__field_values__.values(), types)
    )
