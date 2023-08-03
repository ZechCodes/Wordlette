import weakref
from asyncio import Future
from collections import deque
from typing import Generic, TypeVar

T = TypeVar("T")


class EventStream(Generic[T]):
    def __init__(self):
        self.iterators: weakref.WeakSet[EventStreamIterator] = weakref.WeakSet()
        self.stopped = False

    def __aiter__(self) -> "EventStreamIterator[T]":
        iterator = EventStreamIterator()
        if self.stopped:
            iterator.stop()

        self.iterators.add(iterator)
        return iterator

    def send(self, event: T):
        future = Future()
        future.set_result(event)
        for watcher in self.iterators:
            watcher.send(future)

    def stop(self):
        self.stopped = True
        for watcher in self.iterators:
            watcher.stop()


class EventStreamIterator(Generic[T]):
    def __init__(self):
        self.queue = deque()
        self.next = None

    def __aiter__(self) -> "EventStreamIterator[T]":
        return self

    def __anext__(self) -> Future[T]:
        if self.next:
            next_, self.next = self.next, None
            return next_

        if self.queue:
            return self.queue.popleft()

        self.next = Future()
        return self.next

    def send(self, future: Future[T]):
        if self.next:
            self.next.set_result(future.result())
            self.next = None

        else:
            self.queue.append(future)

    def stop(self):
        if self.next:
            self.next.set_exception(StopAsyncIteration)

        else:
            future = Future()
            future.set_exception(StopAsyncIteration)
            self.queue.append(future)
