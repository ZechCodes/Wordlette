import unittest.mock as mock

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
    events.observe(mock_observer)
    await events.emit(mock_event)

    assert mock_observer.call_args.args[0] == mock_event


@pytest.mark.asyncio
async def test_observable():
    mock_event, mock_listener = mock.Mock(), mock.AsyncMock()

    class ObservableType(Observable):
        pass

    observable = ObservableType()
    observable.on(type(mock_event), mock_listener)
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
