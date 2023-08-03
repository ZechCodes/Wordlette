import weakref

from wordlette.events.event_streams import EventStream
from wordlette.events.events import Event


class Observable:
    def __init__(self):
        self._event_stream = None

    def __del__(self):
        self.stop()

    @property
    def event_stream(self) -> EventStream:
        if not (event_stream := self._get_event_stream()):
            self._event_stream = weakref.ref(event_stream := EventStream())

        return event_stream

    def emit(self, event: Event):
        if event_stream := self._get_event_stream():
            event_stream.send(event)

    def stop(self):
        if event_stream := self._get_event_stream():
            event_stream.stop()
            self._event_stream = None

    def _get_event_stream(self) -> EventStream | None:
        return self._event_stream() if self._event_stream else None
