from typing import Annotated

import pytest

from wordlette.models import FieldSchema, Model, ValidationError


def test_model_schemas():
    class TestModel(Model):
        id: int @ FieldSchema()
        name: str @ FieldSchema()

    assert TestModel.id.name == "id"
    assert TestModel.id.type is int

    assert TestModel.name.name == "name"
    assert TestModel.name.type is str


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
