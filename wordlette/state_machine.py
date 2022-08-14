from __future__ import annotations
import asyncio

from typing import Awaitable, Callable, overload, Type, TypeAlias

from functools import cache
from inspect import iscoroutinefunction
from wordlette.exceptions import (
    WordletteTransitionFailed,
    WordletteTransitionImpossible,
)
from asyncio import Future

StateRunCallable: TypeAlias = Callable[["StateMachine"], Awaitable | None]


StateTransitionCallable: TypeAlias = Callable[["StateMachine"], Awaitable | None]


def _make_coroutine(func):
    async def coroutine(*args, **kwargs):
        return func(*args, **kwargs) if func else None

    return coroutine


class MappingDescriptor:
    @cache
    def __get(self, owner):
        return {}

    def __get__(self, instance, owner) -> dict:
        return self.__get(owner)


class StateMachine:
    __states__: dict[State, StateRunCallable] = MappingDescriptor()
    __transitions__: dict[tuple[State, State], Transition] = MappingDescriptor()

    def __init__(self, initial_state: State, *, loop=None):
        self._current_state: State | None = None
        self._next_state_change: Future = Future()

        (loop or asyncio.get_event_loop()).create_task(
            self._set_current_state(initial_state)
        )

    def __await__(self):
        yield from self._next_state_change.__await__()
        return self

    @property
    def state(self) -> State:
        return self._current_state

    async def to(self, new_state: State):
        transition = self.__transitions__.get((self._current_state, new_state))
        if not transition:
            raise WordletteTransitionImpossible(
                f"Cannot transition from {self._current_state} to {new_state}"
            )

        await transition.run(self)
        await self._set_current_state(new_state)

    async def _set_current_state(self, new_state: State):
        self._current_state = new_state
        if run := self.__states__[self._current_state]:
            await run(self)

        self._next_state_change, future = Future(), self._next_state_change
        future.set_result(new_state)

    @classmethod
    def add_state(cls, state: State, run: StateRunCallable):
        cls.__states__[state] = (
            run if iscoroutinefunction(run) else _make_coroutine(run)
        )

    @classmethod
    def add_transition(cls, transition: Transition):
        cls.__transitions__[transition.from_state, transition.to_state] = transition


class State:
    def __init__(self):
        self.name = "<UNNAMED>"

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f"<{type(self).__name__}:{self.name}>"


class StateDescriptor:
    def __init__(self, run: StateRunCallable | None = None):
        self.run: StateRunCallable = run
        self.state = State()

    def __get__(self, instance, owner) -> State:
        return self.state

    def __rshift__(
        self, to_state: StateDescriptor
    ) -> Callable[[StateTransitionCallable], Transition]:
        def create_transition_descriptor(
            transition: StateTransitionCallable,
        ) -> Transition:
            return Transition(self.state, to_state.state, transition)

        return create_transition_descriptor

    def __set_name__(self, owner: StateMachine, name):
        self.state.name = name
        owner.add_state(self.state, self.run)


class Transition:
    def __init__(
        self, from_state: State, to_state: State, transition: StateTransitionCallable
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.transition = (
            transition
            if iscoroutinefunction(transition)
            else _make_coroutine(transition)
        )

    async def run(self, state_machine: StateMachine):
        try:
            await self.transition(state_machine)
        except Exception as exception:
            raise WordletteTransitionFailed(
                f"When attempting to transition from {self.from_state} to {self.to_state} an exception was raised"
            ) from exception

    def __repr__(self):
        return f"<Transition: from={self.from_state} to={self.to_state}>"

    def __set_name__(self, owner: StateMachine, name):
        owner.add_transition(self)


def state(run: StateRunCallable | None = None) -> StateDescriptor:
    return StateDescriptor(run)
