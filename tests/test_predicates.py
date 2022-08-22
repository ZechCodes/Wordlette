from wordlette.predicates import predicate as _predicate
import pytest


@pytest.mark.asyncio
async def test_predicate():
    @_predicate
    def predicate(value):
        return value == 5

    assert not await predicate(10)
    assert await predicate(5)


@pytest.mark.asyncio
async def test_inverse_predicate():
    @_predicate
    def predicate(value):
        return value == 5

    not_predicate = ~predicate
    assert await not_predicate(10)
    assert not await not_predicate(5)


@pytest.mark.asyncio
async def test_and_predicate():
    @_predicate
    def predicate_5(value):
        return value % 5 == 0

    @_predicate
    def predicate_2(value):
        return value % 2 == 0

    predicate_2_5 = predicate_2 & predicate_5
    assert await predicate_2_5(10)
    assert not await predicate_2_5(5)


@pytest.mark.asyncio
async def test_or_predicate():
    @_predicate
    def predicate_5(value):
        return value % 5 == 0

    @_predicate
    def predicate_2(value):
        return value % 2 == 0

    predicate_2_5 = predicate_2 | predicate_5
    assert await predicate_2_5(2)
    assert await predicate_2_5(5)
    assert not await predicate_2_5(7)
