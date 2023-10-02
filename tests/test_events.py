import unittest.mock as mock
from typing import cast

import pytest

from wordlette.events import Observable, Observer
from wordlette.events.dispatch import EventDispatch
from wordlette.events.events import Event


@pytest.mark.asyncio
async def test_event_dispatch():
    mock_event, mock_listener = mock.Mock(), mock.AsyncMock()

    events = EventDispatch()
    events.listen(type(mock_event), mock_listener)

    mock_listener.reset_mock()
    await events.emit(mock_event)

    assert mock_listener.call_args.args[0] == mock_event


@pytest.mark.asyncio
async def test_event_dispatch_after():
    mock_obj, mock_event = mock.Mock(), mock.Mock()
    mock_obj.listener, mock_obj.after = mock.AsyncMock(), mock.AsyncMock()

    events = EventDispatch()
    events.listen(type(mock_event), mock_obj.listener)
    events.after(type(mock_event), mock_obj.after)

    mock_obj.reset_mock()
    await events.emit(mock_event)

    assert mock_obj.mock_calls == [
        mock.call.listener(mock_event),
        mock.call.after(mock_event),
    ]


@pytest.mark.asyncio
async def test_event_dispatch_before():
    mock_obj, mock_event = mock.Mock(), mock.Mock()
    mock_obj.listener, mock_obj.before = mock.AsyncMock(), mock.AsyncMock()

    events = EventDispatch()
    events.listen(type(mock_event), mock_obj.listener)
    events.before(type(mock_event), mock_obj.before)

    mock_obj.reset_mock()
    await events.emit(mock_event)

    assert mock_obj.mock_calls == [
        mock.call.before(mock_event),
        mock.call.listener(mock_event),
    ]


@pytest.mark.asyncio
async def test_event_listener_stop():
    mock_event, mock_listener = mock.Mock(), mock.AsyncMock()

    events = EventDispatch()
    events.listen(type(mock_event), mock_listener)
    events.stop(type(mock_event), mock_listener)

    mock_listener.reset_mock()
    await events.emit(mock_event)

    assert mock_listener.called is False


@pytest.mark.asyncio
async def test_disptach_observers():
    mock_event, mock_observer = mock.Mock(), mock.AsyncMock()

    events = EventDispatch()
    events.propagate_to(mock_observer)
    await events.emit(mock_event)

    assert mock_observer.call_args.args[0] == mock_event


@pytest.mark.asyncio
async def test_observable():
    mock_event, mock_listener = mock.Mock(), mock.AsyncMock()

    class ObservableType(Observable):
        pass

    observable = ObservableType()
    observable.listen(cast(Event, type(mock_event)), mock_listener)
    await observable.emit(mock_event)

    assert mock_listener.called is True


@pytest.mark.asyncio
async def test_observer_event_detection():
    class ObserverType(Observer):
        async def listener(self, event: Event):
            ...

    assert Event in ObserverType.__event_listeners__


@pytest.mark.asyncio
async def test_observer_listener():
    class ObservableType(Observable):
        pass

    class ObserverType(Observer):
        ...

    mock_event, mock_listener = mock.Mock(), mock.AsyncMock()
    ObserverType.__event_listeners__[type(mock_event)] = mock_listener

    observable = ObservableType()
    observer = ObserverType()
    observer.observe(observable)

    await observable.emit(mock_event)
    assert mock_listener.called is True


@pytest.mark.asyncio
async def test_instance_to_type_emit_propagation():
    class ObservableType(Observable):
        pass

    mock_listener, mock_event = mock.AsyncMock(), mock.Mock()
    observable = ObservableType()

    ObservableType.listen(type(mock_event), mock_listener)
    await observable.emit(mock_event)

    assert mock_listener.call_count == 1


@pytest.mark.asyncio
async def test_instance_to_super_type_emit_propagation():
    class SuperObservableType(Observable):
        pass

    class ObservableType(SuperObservableType):
        pass

    mock_listener, mock_event = mock.AsyncMock(), mock.Mock()
    observable = ObservableType()

    SuperObservableType.listen(type(mock_event), mock_listener)
    await observable.emit(mock_event)

    assert mock_listener.call_count == 1


@pytest.mark.asyncio
async def test_type_to_instance_emit_propagation():
    class ObservableType(Observable):
        pass

    mock_listener, mock_event = mock.AsyncMock(), mock.Mock()
    observable = ObservableType()

    observable.listen(type(mock_event), mock_listener)
    await ObservableType.emit(mock_event)

    assert mock_listener.call_count == 1


@pytest.mark.asyncio
async def test_super_type_to_instance_emit_propagation():
    class SuperObservableType(Observable):
        pass

    class ObservableType(SuperObservableType):
        pass

    mock_listener, mock_event = mock.AsyncMock(), mock.Mock()
    observable = ObservableType()

    observable.listen(type(mock_event), mock_listener)
    await SuperObservableType.emit(mock_event)

    assert mock_listener.call_count == 1


@pytest.mark.asyncio
async def test_instance_to_mro_emit_propagation():
    class SuperObservableType(Observable):
        pass

    class ObservableType(SuperObservableType):
        pass

    mock_event, mock_group = mock.Mock(), mock.Mock()
    mock_group.a, mock_group.b, mock_group.c = (
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
    )
    observable = ObservableType()

    SuperObservableType.listen(type(mock_event), mock_group.c)
    ObservableType.listen(type(mock_event), mock_group.b)
    observable.listen(type(mock_event), mock_group.a)

    mock_group.reset_mock()
    await observable.emit(mock_event)

    assert mock_group.mock_calls == [
        mock.call.a(mock_event),
        mock.call.b(mock_event),
        mock.call.c(mock_event),
    ]


@pytest.mark.asyncio
async def test_type_to_mro_emit_propagation():
    class SuperObservableType(Observable):
        pass

    class ObservableType(SuperObservableType):
        pass

    mock_event, mock_group = mock.Mock(), mock.Mock()
    mock_group.a, mock_group.b, mock_group.c = (
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
    )
    observable = ObservableType()

    SuperObservableType.listen(type(mock_event), mock_group.c)
    ObservableType.listen(type(mock_event), mock_group.b)
    observable.listen(type(mock_event), mock_group.a)

    mock_group.reset_mock()
    await ObservableType.emit(mock_event)

    assert mock_group.mock_calls == [
        mock.call.a(mock_event),
        mock.call.b(mock_event),
        mock.call.c(mock_event),
    ]


@pytest.mark.asyncio
async def test_type_emit_listening():
    class ObservableType(Observable):
        pass

    mock_listener, mock_event = mock.AsyncMock(), mock.Mock()

    ObservableType.listen(type(mock_event), mock_listener)
    await ObservableType.emit(mock_event)

    assert mock_listener.call_count == 1


@pytest.mark.asyncio
async def test_advanced_emit_propagation():
    class BaseObservable(Observable):
        ...

    class ChildObservableA(BaseObservable):
        ...

    class ChildObservableB(BaseObservable):
        ...

    class GrandChildObservable(ChildObservableA):
        ...

    base = BaseObservable()
    child_a = ChildObservableA()
    child_b = ChildObservableB()
    grand_child = GrandChildObservable()

    mock_event, mock_group = mock.Mock(), mock.Mock()
    (
        mock_group.base_type,
        mock_group.child_a_type,
        mock_group.child_b_type,
        mock_group.grand_child_type,
        mock_group.base,
        mock_group.child_a,
        mock_group.child_b,
        mock_group.grand_child,
    ) = (
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
    )

    BaseObservable.listen(type(mock_event), mock_group.base_type)
    ChildObservableA.listen(type(mock_event), mock_group.child_a_type)
    ChildObservableB.listen(type(mock_event), mock_group.child_b_type)
    GrandChildObservable.listen(type(mock_event), mock_group.grand_child_type)
    base.listen(type(mock_event), mock_group.base)
    child_a.listen(type(mock_event), mock_group.child_a)
    child_b.listen(type(mock_event), mock_group.child_b)
    grand_child.listen(type(mock_event), mock_group.grand_child)

    mock_group.reset_mock()
    await BaseObservable.emit(mock_event)
    assert sorted(mock_group.mock_calls[:4]) == sorted(
        [
            mock.call.base(mock_event),
            mock.call.child_a(mock_event),
            mock.call.child_b(mock_event),
            mock.call.grand_child(mock_event),
        ]
    )
    assert sorted(mock_group.mock_calls[4:7]) == sorted(
        [
            mock.call.grand_child_type(mock_event),
            mock.call.child_a_type(mock_event),
            mock.call.child_b_type(mock_event),
        ]
    )
    assert mock_group.mock_calls[~0] == mock.call.base_type(mock_event)

    mock_group.reset_mock()
    await ChildObservableA.emit(mock_event)
    assert sorted(mock_group.mock_calls[:2]) == sorted(
        [
            mock.call.child_a(mock_event),
            mock.call.grand_child(mock_event),
        ]
    )
    assert sorted(mock_group.mock_calls[2:~0]) == sorted(
        [
            mock.call.grand_child_type(mock_event),
            mock.call.child_a_type(mock_event),
        ]
    )
    assert mock_group.mock_calls[~0] == mock.call.base_type(mock_event)

    mock_group.reset_mock()
    await ChildObservableB.emit(mock_event)
    assert mock_group.mock_calls == [
        mock.call.child_b(mock_event),
        mock.call.child_b_type(mock_event),
        mock.call.base_type(mock_event),
    ]

    mock_group.reset_mock()
    await GrandChildObservable.emit(mock_event)
    assert mock_group.mock_calls == [
        mock.call.grand_child(mock_event),
        mock.call.grand_child_type(mock_event),
        mock.call.child_a_type(mock_event),
        mock.call.base_type(mock_event),
    ]

    mock_group.reset_mock()
    await grand_child.emit(mock_event)
    assert mock_group.mock_calls == [
        mock.call.grand_child(mock_event),
        mock.call.grand_child_type(mock_event),
        mock.call.child_a_type(mock_event),
        mock.call.base_type(mock_event),
    ]

    mock_group.reset_mock()
    await child_a.emit(mock_event)
    assert mock_group.mock_calls == [
        mock.call.child_a(mock_event),
        mock.call.child_a_type(mock_event),
        mock.call.base_type(mock_event),
    ]

    mock_group.reset_mock()
    await child_b.emit(mock_event)
    assert mock_group.mock_calls == [
        mock.call.child_b(mock_event),
        mock.call.child_b_type(mock_event),
        mock.call.base_type(mock_event),
    ]

    mock_group.reset_mock()
    await base.emit(mock_event)
    assert mock_group.mock_calls == [
        mock.call.base(mock_event),
        mock.call.base_type(mock_event),
    ]


@pytest.mark.asyncio
async def test_event_type_sub_class():
    class TestEvent(Event):
        ...

    class TestSubEvent(TestEvent):
        ...

    mock_listener = mock.AsyncMock()

    events = EventDispatch()
    events.listen(TestEvent, mock_listener)

    mock_listener.reset_mock()
    await events.emit(event := TestSubEvent())

    assert mock_listener.call_args.args[0] == event
