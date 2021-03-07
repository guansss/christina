import asyncio

from pymitter import EventEmitter as BaseEventEmitter


class EventEmitter(BaseEventEmitter):
    def __init__(self, wildcard=False, new_listener=False, max_listeners=-1, delimiter="."):
        super().__init__(wildcard=wildcard, new_listener=new_listener, max_listeners=max_listeners, delimiter=delimiter)

        self.loop = asyncio.get_event_loop()

    # emit event in thread in which this emitter is created
    def emit_threading(self, event, *args):
        self.loop.call_soon_threadsafe(super().emit, event, *args)
