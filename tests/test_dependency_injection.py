from dataclasses import dataclass

from bevy import get_repository, Repository
from pytest_asyncio import fixture

from wordlette.at_annotateds import AtProvider, AtAnnotation
from wordlette.utils.dependency_injection import (
    inject_dependencies,
    inject,
    AutoInject,
)


@fixture
def repo():
    old = get_repository()
    repo = Repository.factory()
    repo.add_providers(AtProvider())
    Repository.set_repository(repo)
    yield repo
    Repository.set_repository(old)


def test_function_param_injection(repo: Repository):
    @dataclass
    class Dep:
        message: str

    @inject_dependencies
    def func(dep: Dep @ inject) -> str:
        return dep.message

    repo.set(Dep, Dep("hello"))
    assert func() == "hello"


def test_custom_injector_types(repo):
    class TestInjector(AtAnnotation):
        def __init__(self, message: str):
            self.message = message

        def strategy(self, type_, _):
            return lambda: type_(self.message)

    @inject_dependencies
    def func(dep: str @ TestInjector("hello")) -> str:
        return dep

    assert func() == "hello"


def test_auto_inject_class(repo):
    class TestClass(AutoInject):
        def function(self, dep: str @ inject = "") -> str:
            return dep

    repo.set(str, "hello")
    assert TestClass().function() == "hello"


def test_auto_inject_class_functions_only_with_dependencies():
    class TestClass(AutoInject):
        def function(self, dep: str @ inject = "") -> str:
            ...

        def no_dep_function(self):
            ...

    assert hasattr(TestClass.function, "injected_params")
    assert not hasattr(TestClass.no_dep_function, "injected_params")


def test_auto_inject_class_annotations():
    class Dep:
        ...

    class TestClass(AutoInject):
        dep: Dep @ inject

    inst_a = TestClass()
    inst_b = TestClass()
    assert isinstance(inst_a.dep, Dep)
    assert inst_a.dep is inst_b.dep
