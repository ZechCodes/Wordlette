from dataclasses import dataclass

from bevy import get_repository, Repository
from pytest_asyncio import fixture

from wordlette.at_annotateds import AtProvider, AtAnnotation
from wordlette.utils.dependency_injection import inject, dependency, AutoInject


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

    @inject
    def func(dep: Dep @ dependency) -> str:
        return dep.message

    repo.set(Dep, Dep("hello"))
    assert func() == "hello"


def test_custom_injector_types(repo):
    class TestInjector(AtAnnotation):
        def __init__(self, message: str):
            self.message = message

        def strategy(self, type_, _):
            return lambda: type_(self.message)

    @inject
    def func(dep: str @ TestInjector("hello")) -> str:
        return dep

    assert func() == "hello"


def test_auto_inject_class(repo):
    class TestClass(AutoInject):
        def function(self, dep: str @ dependency = "") -> str:
            return dep

    repo.set(str, "hello")
    assert TestClass().function() == "hello"
