from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Awaitable

from pydantic import BaseModel, Field
from .tool import tool

# ---------------------------------------------------------------------------
# Event model
# ---------------------------------------------------------------------------

def _current_timestamp_ms() -> int:
    """Return current UTC timestamp in milliseconds."""
    return int(datetime.utcnow().timestamp() * 1000)


class Event(BaseModel):
    """Generic event model with automatic UTC timestamp in milliseconds."""

    type: str
    payload: dict[str, Any]
    timestamp: int = Field(default_factory=_current_timestamp_ms)

    class Config:
        extra = "ignore"
        populate_by_name = True


# ---------------------------------------------------------------------------
# Storage hooks — declare only, you will implement them
# ---------------------------------------------------------------------------

async def fetch_new_events(after:int) -> list[Event]:
    """Retrieve and return *new* events not yet processed."""
    from cogni import State
    State.reset_cache()
    if not "events" in State['events']:
        return []
    #print(State['events'])
    all_events = [
        e for e in State['events']['events'].to_dict() if e.get('timestamp')]
    #print(all_events)
    #print(all_events)
    new_events = [Event(**evt) for evt in all_events if evt['timestamp'] > after]
    sorted_events = sorted(new_events, key=lambda x: x.timestamp)
    
    return sorted_events


def store_event(event: Event) -> None:
    """Persist an event for later consumption."""
    from cogni import State
    State.reset_cache()
    if not "events" in State['events']:
        State['events']['events'] = []
        
    if not event.type:
        print(event)
        raise Exception('a')
    try:
        State['events']['events'].append(event.model_dump(exclude_unset=False))
    except:
        ...

@tool
def emit(type:str, payload:dict[str, Any]) -> None:
    event = Event(type=type, payload=payload)
    store_event(event)



# ---------------------------------------------------------------------------
# ES (Event Stream) – simple async dispatcher
# ---------------------------------------------------------------------------


Handler = Callable[[Event], Awaitable[None] | None]


class _ES:
    """In-memory event dispatcher with async background listener."""

    def __init__(self, poll_interval: float = 0.1) -> None:
        from .state import State
        self._poll_interval = poll_interval
        self._handlers: dict[str, list[Handler]] = {}
        self._wildcard_handlers: list[Handler] = []
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self.watch_only = False
        if "last_event" not in State["events"]:
            State["events"]["last_event"] = 0
            
        self._last_handle = State["events"]["last_event"]
    @property
    def last_event(self):
        from .state import State
        key = "last_event"
        if self.watch_only:
            key += "_watch"
        if key not in State["events"]:
            State["events"][key] = 0
        return State["events"][key]
    
    @last_event.setter
    def last_event(self, val):
        from .state import State
        key = "last_event"
        if self.watch_only:
            key += "_watch"

        State["events"][key] = val

    # ---------------------------------------------------------------------
    # Registration API
    # ---------------------------------------------------------------------
    def on(self, event_type: str, handler: Handler) -> None:
        """Register *handler* for *event_type* (or "*" for any event)."""
        container = (
            self._wildcard_handlers
            if event_type == "*"
            else self._handlers.setdefault(event_type, [])
        )
        container.append(self._ensure_async(handler))

    @staticmethod
    def _ensure_async(handler: Handler) -> Callable[[Event], Awaitable[None]]:
        if asyncio.iscoroutinefunction(handler):
            return handler  # type: ignore[return-value]

        async def _wrapper(evt: Event) -> None:  # type: ignore[valid-type]
            handler(evt)  # type: ignore[misc]

        return _wrapper

    # ---------------------------------------------------------------------
    # Runtime control
    # ---------------------------------------------------------------------
    async def _dispatch(self, evt: Event) -> None:
        for h in self._wildcard_handlers:
            res = h(evt)
            if asyncio.iscoroutine(res):
                await res
        for h in self._handlers.get(evt.type, []):
            res = h(evt)
            if asyncio.iscoroutine(res):
                await res

    async def _loop(self) -> None:
        from cogni import State
        State.reset_cache()


        while self._running:
            try:
                events = await fetch_new_events(self.last_event)
            except Exception as E:  # pragma: no cover
                print(E)
                raise
                events = []
            for evt in events:
                await self._dispatch(evt)

                self.last_event = evt.timestamp

            await asyncio.sleep(self._poll_interval)

    def start(self) -> None:
        """Kick off the background polling task (idempotent)."""
        if self._task is None or self._task.done():
            self._running = True          # ← moved here, prevents race
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the polling loop and wait for completion."""
        self._running = False
        if self._task:
            await self._task              # wait for graceful exit
            self._task = None

    # ---------------------------------------------------------------------
    # Convenience: emit helper
    # ---------------------------------------------------------------------
    def emit(self, event_type: str, payload: dict[str, Any]) -> Event:
        evt = Event(type=event_type, payload=payload)
        store_event(evt)
        return evt
        return evt
    
ES= _ES(0.1)

def on(event, callback=None):
    def _decorator(func):
        def _inner(event):
            func(event)
            if callback:
                callback()
        ES.on(event, _inner)
        return _inner
    return _decorator